"""Soft Actor-Critic (SAC) implementation in pure NumPy for Bay 1 Cleanroom.

Theoretical foundations:
1. Haarnoja et al. (2018): Maximum Entropy RL with Gaussian stochastic actor and Double-Q critics.
2. Ding et al. (2024, CLUE): Epistemic uncertainty quantification via Double-Q critic disagreement.
3. Kumar et al. (2023): Action Masking integration.
4. Silvestri et al. (2024, ETH Zurich): Simulation-to-real pre-training and deterministic inference.
"""

import json
from pathlib import Path
import numpy as np


FEATURE_NAMES = (
    "dp", "particle_count", "particles_05", "temp", "rh", "amc_nh3", "mau_filter_dp",
    "mes_load_kw", "particle_source", "current_exhaust", "door_fraction",
    "outdoor_temp", "outdoor_rh", "amc_multiplier", "prev_mau", "prev_ffu", "mau_floor",
    "exhaust_step_1", "exhaust_step_2", "exhaust_step_3", "exhaust_step_4", "exhaust_step_5",
    "mes_load_step_1", "mes_load_step_2", "mes_load_step_3", "mes_load_step_4", "mes_load_step_5",
    "temp_velocity", "dp_velocity",
)

SENSOR_FEATURES = ("dp", "particle_count", "particles_05", "temp", "rh", "amc_nh3", "mau_filter_dp")

STATE_MEAN = np.array([
    18.0, 150.0, 15.0, 22.0, 43.0, 0.2, 180.0,
    60.0, 50000.0, 2.0, 0.05,
    30.0, 65.0, 0.5, 0.65, 0.65, 0.55,
    2.0, 2.0, 2.0, 2.0, 2.0,
    60.0, 60.0, 60.0, 60.0, 60.0,
    0.0, 0.0,
], dtype=np.float64)

STATE_STD = np.array([
    5.0, 200.0, 15.0, 1.0, 5.0, 0.3, 50.0,
    35.0, 70000.0, 0.8, 0.15,
    6.0, 15.0, 0.5, 0.2, 0.2, 0.15,
    0.8, 0.8, 0.8, 0.8, 0.8,
    35.0, 35.0, 35.0, 35.0, 35.0,
    0.5, 2.0,
], dtype=np.float64)


def extract_sac_features(sensors, disturbance, upcoming, mau_floor, prev_mau, prev_ffu,
                         temp_velocity=0.0, dp_velocity=0.0):
    """Extract and vectorize the 29 state features required by the SAC Agent (Biemann et al., 2021)."""
    features = [
        *(sensors[key] for key in SENSOR_FEATURES),
        disturbance.equipment_kw,
        disturbance.particles_per_min,
        disturbance.exhaust_m3_s,
        disturbance.door_fraction,
        disturbance.outdoor_temp_c,
        disturbance.outdoor_rh_pct,
        disturbance.amc_multiplier,
        prev_mau,
        prev_ffu,
        mau_floor,
    ]
    # Forecast steps (5 future steps for exhaust and equipment load)
    for offset in range(1, 6):
        item = upcoming[offset] if offset < len(upcoming) else upcoming[-1]
        features.append(item.exhaust_m3_s)
    for offset in range(1, 6):
        item = upcoming[offset] if offset < len(upcoming) else upcoming[-1]
        features.append(item.equipment_kw)

    # Dynamic physical velocities (Biemann et al., 2021 Section 6.6)
    features.append(float(temp_velocity))
    features.append(float(dp_velocity))

    return np.array(features, dtype=np.float64)


def normalize_state(s):
    return (np.asarray(s, dtype=np.float64) - STATE_MEAN) / (STATE_STD + 1e-6)


class DenseLayer:
    """Fully connected neural layer with Xavier initialization and Adam optimizer."""

    def __init__(self, in_dim, out_dim, act="relu", seed=None):
        rng = np.random.default_rng(seed)
        limit = np.sqrt(6.0 / (in_dim + out_dim))
        self.w = rng.uniform(-limit, limit, (in_dim, out_dim)).astype(np.float64)
        self.b = np.zeros(out_dim, dtype=np.float64)
        self.act = act

        # Adam momentum and velocity buffers
        self.mw = np.zeros_like(self.w)
        self.vw = np.zeros_like(self.w)
        self.mb = np.zeros_like(self.b)
        self.vb = np.zeros_like(self.b)
        self.t = 0

    def forward(self, x):
        self.x = x
        self.z = x @ self.w + self.b
        if self.act == "relu":
            self.a = np.maximum(0.0, self.z)
        elif self.act == "tanh":
            self.a = np.tanh(self.z)
        else:
            self.a = self.z
        return self.a

    def backward(self, da):
        if self.act == "relu":
            dz = da * (self.z > 0.0)
        elif self.act == "tanh":
            dz = da * (1.0 - np.square(self.a))
        else:
            dz = da
        self.dw = self.x.T @ dz
        self.db = np.sum(dz, axis=0)
        dx = dz @ self.w.T
        return dx

    def step(self, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self.t += 1
        self.mw = beta1 * self.mw + (1.0 - beta1) * self.dw
        self.vw = beta2 * self.vw + (1.0 - beta2) * np.square(self.dw)
        m_hat = self.mw / (1.0 - beta1 ** self.t)
        v_hat = self.vw / (1.0 - beta2 ** self.t)
        self.w -= lr * m_hat / (np.sqrt(v_hat) + eps)

        self.mb = beta1 * self.mb + (1.0 - beta1) * self.db
        self.vb = beta2 * self.vb + (1.0 - beta2) * np.square(self.db)
        mb_hat = self.mb / (1.0 - beta1 ** self.t)
        vb_hat = self.vb / (1.0 - beta2 ** self.t)
        self.b -= lr * mb_hat / (np.sqrt(vb_hat) + eps)

    def to_dict(self):
        return {"w": self.w.tolist(), "b": self.b.tolist(), "act": self.act}

    @classmethod
    def from_dict(cls, data):
        w = np.array(data["w"], dtype=np.float64)
        b = np.array(data["b"], dtype=np.float64)
        layer = cls(w.shape[0], w.shape[1], act=data.get("act", "relu"))
        layer.w = w
        layer.b = b
        layer.mw = np.zeros_like(w)
        layer.vw = np.zeros_like(w)
        layer.mb = np.zeros_like(b)
        layer.vb = np.zeros_like(b)
        return layer


class GaussianActor:
    """Stochastic Gaussian Actor with squashed Tanh output: a = tanh(mu + sigma * eps)."""

    def __init__(self, state_dim=29, action_dim=2, hidden_dim=64, seed=42):
        self.l1 = DenseLayer(state_dim, hidden_dim, act="relu", seed=seed)
        self.l2 = DenseLayer(hidden_dim, hidden_dim, act="relu", seed=seed + 1 if seed else None)
        self.mu_head = DenseLayer(hidden_dim, action_dim, act="linear", seed=seed + 2 if seed else None)
        self.log_std_head = DenseLayer(hidden_dim, action_dim, act="linear", seed=seed + 3 if seed else None)
        self.action_dim = action_dim

    def forward(self, state):
        h1 = self.l1.forward(state)
        h2 = self.l2.forward(h1)
        mu = self.mu_head.forward(h2)
        log_std = np.clip(self.log_std_head.forward(h2), -20.0, 2.0)
        return mu, log_std

    def sample(self, state, reparameterize=True, seed=None):
        state = np.atleast_2d(state)
        mu, log_std = self.forward(state)
        std = np.exp(log_std)

        if reparameterize:
            rng = np.random.default_rng(seed)
            eps = rng.normal(size=mu.shape)
            z = mu + std * eps
        else:
            z = mu

        action = np.tanh(z)

        # Log-probability calculation under Tanh squashing
        var = np.square(std)
        log_gauss = -0.5 * (np.square(z - mu) / (var + 1e-8) + 2.0 * log_std + np.log(2.0 * np.pi))
        log_prob = np.sum(log_gauss - np.log(1.0 - np.square(action) + 1e-6), axis=1)

        return action, log_prob, (mu, log_std, z)

    def act_deterministic(self, state):
        state = np.atleast_2d(state)
        mu, _ = self.forward(state)
        return np.tanh(mu)

    def backward(self, d_mu, d_log_std):
        d_h2_mu = self.mu_head.backward(d_mu)
        d_h2_std = self.log_std_head.backward(d_log_std)
        d_h2 = d_h2_mu + d_h2_std
        d_h1 = self.l2.backward(d_h2)
        d_x = self.l1.backward(d_h1)
        return d_x

    def step(self, lr=3e-4):
        self.l1.step(lr)
        self.l2.step(lr)
        self.mu_head.step(lr)
        self.log_std_head.step(lr)

    def to_dict(self):
        return {
            "l1": self.l1.to_dict(), "l2": self.l2.to_dict(),
            "mu_head": self.mu_head.to_dict(), "log_std_head": self.log_std_head.to_dict(),
        }

    @classmethod
    def from_dict(cls, data):
        actor = cls(state_dim=1, action_dim=1, hidden_dim=1)
        actor.l1 = DenseLayer.from_dict(data["l1"])
        actor.l2 = DenseLayer.from_dict(data["l2"])
        actor.mu_head = DenseLayer.from_dict(data["mu_head"])
        actor.log_std_head = DenseLayer.from_dict(data["log_std_head"])
        actor.action_dim = actor.mu_head.w.shape[1]
        return actor


class Critic:
    """State-Action Q-network."""

    def __init__(self, state_dim=29, action_dim=2, hidden_dim=64, seed=42):
        self.l1 = DenseLayer(state_dim + action_dim, hidden_dim, act="relu", seed=seed)
        self.l2 = DenseLayer(hidden_dim, hidden_dim, act="relu", seed=seed + 1 if seed else None)
        self.out = DenseLayer(hidden_dim, 1, act="linear", seed=seed + 2 if seed else None)

    def forward(self, state, action):
        sa = np.hstack([state, action])
        h1 = self.l1.forward(sa)
        h2 = self.l2.forward(h1)
        q = self.out.forward(h2)
        return q

    def backward(self, dq):
        d_h2 = self.out.backward(dq)
        d_h1 = self.l2.backward(d_h2)
        d_sa = self.l1.backward(d_h1)
        return d_sa

    def step(self, lr=1e-3):
        self.l1.step(lr)
        self.l2.step(lr)
        self.out.step(lr)

    def to_dict(self):
        return {"l1": self.l1.to_dict(), "l2": self.l2.to_dict(), "out": self.out.to_dict()}

    @classmethod
    def from_dict(cls, data):
        c = cls(state_dim=1, action_dim=1, hidden_dim=1)
        c.l1 = DenseLayer.from_dict(data["l1"])
        c.l2 = DenseLayer.from_dict(data["l2"])
        c.out = DenseLayer.from_dict(data["out"])
        return c


class ReplayBuffer:
    """Circular experience replay buffer for off-policy SAC learning."""

    def __init__(self, max_size=50000, state_dim=29, action_dim=2):
        self.max_size = max_size
        self.ptr = 0
        self.size = 0
        self.states = np.zeros((max_size, state_dim), dtype=np.float64)
        self.actions = np.zeros((max_size, action_dim), dtype=np.float64)
        self.rewards = np.zeros((max_size, 1), dtype=np.float64)
        self.next_states = np.zeros((max_size, state_dim), dtype=np.float64)
        self.dones = np.zeros((max_size, 1), dtype=np.float64)


    def add(self, s, a, r, s_prime, done):
        self.states[self.ptr] = s
        self.actions[self.ptr] = a
        self.rewards[self.ptr] = r
        self.next_states[self.ptr] = s_prime
        self.dones[self.ptr] = float(done)
        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size=64, seed=None):
        rng = np.random.default_rng(seed)
        indices = rng.choice(self.size, size=batch_size, replace=False)
        return (
            self.states[indices],
            self.actions[indices],
            self.rewards[indices],
            self.next_states[indices],
            self.dones[indices],
        )


class SACAgent:
    """Full Soft Actor-Critic agent with Double-Q Critics and Epistemic Uncertainty Estimation."""

    def __init__(self, state_dim=29, action_dim=2, hidden_dim=64, alpha=0.05, gamma=0.99, tau=0.005, seed=42):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.alpha = alpha
        self.log_alpha = float(np.log(max(1e-4, alpha)))
        self.target_entropy = -float(action_dim)
        self.alpha_lr = 3e-4
        self.gamma = gamma
        self.tau = tau

        self.actor = GaussianActor(state_dim, action_dim, hidden_dim, seed=seed)
        self.critic1 = Critic(state_dim, action_dim, hidden_dim, seed=seed + 10)
        self.critic2 = Critic(state_dim, action_dim, hidden_dim, seed=seed + 20)

        self.target_critic1 = Critic(state_dim, action_dim, hidden_dim, seed=seed + 10)
        self.target_critic2 = Critic(state_dim, action_dim, hidden_dim, seed=seed + 20)
        self.soft_target_update(tau=1.0)  # Hard copy at initialization

        self.buffer = ReplayBuffer(max_size=50000, state_dim=state_dim, action_dim=action_dim)

    def soft_target_update(self, tau=None):
        tau = self.tau if tau is None else tau
        for target, source in [(self.target_critic1, self.critic1), (self.target_critic2, self.critic2)]:
            for t_layer, s_layer in [(target.l1, source.l1), (target.l2, source.l2), (target.out, source.out)]:
                t_layer.w = tau * s_layer.w + (1.0 - tau) * t_layer.w
                t_layer.b = tau * s_layer.b + (1.0 - tau) * t_layer.b

    def get_action(self, state, deterministic=True):
        norm_s = normalize_state(state)
        if deterministic:
            return self.actor.act_deterministic(norm_s)[0]
        action, _, _ = self.actor.sample(norm_s, reparameterize=True)
        return action[0]

    def evaluate_uncertainty(self, state, action):
        """Quantify epistemic uncertainty via Double-Q critic disagreement (Ding et al., CLUE 2024)."""
        norm_s = np.atleast_2d(normalize_state(state))
        act = np.atleast_2d(action)
        q1 = self.critic1.forward(norm_s, act)[0, 0]
        q2 = self.critic2.forward(norm_s, act)[0, 0]
        uncertainty = abs(q1 - q2)
        return float(uncertainty), float(min(q1, q2))

    def pretrain_behavioral_cloning(self, states, actions, epochs=50, lr=1e-3, batch_size=64):
        """Pre-train actor via Behavioral Cloning from MPC demonstrations (Kumar et al., 2023; Silvestri et al., 2024)."""
        norm_states = normalize_state(states)
        n = len(states)
        for ep in range(epochs):
            perm = np.random.permutation(n)
            total_loss = 0.0
            for start in range(0, n, batch_size):
                idx = perm[start:start + batch_size]
                b_s = norm_states[idx]
                b_a = actions[idx]

                mu, log_std = self.actor.forward(b_s)
                pred_a = np.tanh(mu)
                loss = np.mean(np.square(pred_a - b_a))
                total_loss += loss * len(idx)

                # Gradient w.r.t mu
                d_pred = 2.0 * (pred_a - b_a) / len(idx)
                d_mu = d_pred * (1.0 - np.square(pred_a))
                d_log_std = np.zeros_like(log_std)

                self.actor.backward(d_mu, d_log_std)
                self.actor.step(lr)

        return float(total_loss / max(1, n))

    def train_step(self, batch_size=64, lr_actor=3e-4, lr_critic=1e-3):
        """Execute one SAC gradient step using off-policy experience from the replay buffer."""
        if self.buffer.size < batch_size:
            return {}

        states, actions, rewards, next_states, dones = self.buffer.sample(batch_size)
        norm_s = normalize_state(states)
        norm_next_s = normalize_state(next_states)

        # 1. Compute Bellman Target
        next_acts, next_log_probs, _ = self.actor.sample(norm_next_s, reparameterize=True)
        q1_target = self.target_critic1.forward(norm_next_s, next_acts)
        q2_target = self.target_critic2.forward(norm_next_s, next_acts)
        min_q_target = np.minimum(q1_target, q2_target) - self.alpha * next_log_probs.reshape(-1, 1)
        y = rewards + self.gamma * (1.0 - dones) * min_q_target

        # 2. Update Critic 1 and Critic 2
        q1 = self.critic1.forward(norm_s, actions)
        q2 = self.critic2.forward(norm_s, actions)
        loss_q1 = 0.5 * np.mean(np.square(q1 - y))
        loss_q2 = 0.5 * np.mean(np.square(q2 - y))

        dq1 = (q1 - y) / batch_size
        dq2 = (q2 - y) / batch_size
        self.critic1.backward(dq1)
        self.critic2.backward(dq2)
        self.critic1.step(lr_critic)
        self.critic2.step(lr_critic)

        # 3. Update Actor with Reparameterization Trick (Haarnoja et al., 2018 Eq. 12-13)
        sampled_acts, sampled_log_probs, (mu, log_std, z) = self.actor.sample(norm_s, reparameterize=True)
        q1_eval = self.critic1.forward(norm_s, sampled_acts)
        q2_eval = self.critic2.forward(norm_s, sampled_acts)
        min_q_eval = np.minimum(q1_eval, q2_eval)

        loss_actor = np.mean(self.alpha * sampled_log_probs.reshape(-1, 1) - min_q_eval)

        # Gradient of -min_Q with respect to action via backprop through the chosen critic
        use_c1 = (q1_eval <= q2_eval).astype(np.float64)
        dq_eval = -1.0 / batch_size
        d_sa1 = self.critic1.backward(dq_eval * use_c1)
        d_sa2 = self.critic2.backward(dq_eval * (1.0 - use_c1))
        d_q_d_act = d_sa1[:, -self.action_dim:] + d_sa2[:, -self.action_dim:]

        # Gradient of entropy term with respect to action
        d_ent_d_act = self.alpha * (2.0 * sampled_acts) / (1.0 - np.square(sampled_acts) + 1e-6) / batch_size
        d_loss_d_act = d_q_d_act + d_ent_d_act

        # Reparameterization chain rule: d_z = d_loss_d_act * (1 - tanh^2(z))
        d_z = d_loss_d_act * (1.0 - np.square(sampled_acts))
        std = np.exp(log_std)
        d_mu = d_z
        d_log_std = d_z * (z - mu)

        self.actor.backward(d_mu, d_log_std)
        self.actor.step(lr_actor)

        # 4. Automatic Temperature Tuning (Haarnoja et al., 2018; Biemann et al., 2021)
        d_log_alpha = -np.mean(sampled_log_probs + self.target_entropy)
        self.log_alpha -= self.alpha_lr * d_log_alpha
        self.log_alpha = float(np.clip(self.log_alpha, -5.0, 0.0))  # alpha in [0.0067, 1.0]
        self.alpha = float(np.exp(self.log_alpha))

        # 5. Soft Target Update
        self.soft_target_update()

        return {
            "loss_q1": float(loss_q1),
            "loss_q2": float(loss_q2),
            "loss_actor": float(loss_actor),
            "mean_q": float(np.mean(q1)),
            "alpha": self.alpha,
        }

    def save_weights(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "model_version": "bay1-sac-v2",
            "state_dim": self.state_dim,
            "action_dim": self.action_dim,
            "alpha": self.alpha,
            "log_alpha": self.log_alpha,
            "actor": self.actor.to_dict(),
            "critic1": self.critic1.to_dict(),
            "critic2": self.critic2.to_dict(),
        }
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    def load_weights(self, path):
        path = Path(path)
        record = json.loads(path.read_text(encoding="utf-8"))
        self.actor = GaussianActor.from_dict(record["actor"])
        self.critic1 = Critic.from_dict(record["critic1"])
        self.critic2 = Critic.from_dict(record["critic2"])
        self.target_critic1 = Critic.from_dict(record["critic1"])
        self.target_critic2 = Critic.from_dict(record["critic2"])
        self.alpha = float(record.get("alpha", self.alpha))
        self.log_alpha = float(record.get("log_alpha", np.log(self.alpha)))
