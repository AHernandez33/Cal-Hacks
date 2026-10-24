"""Privacy-first, synthetic-data federated learning demonstration for SCD.

Run from the project root: python -m backend.federated
This is simulated FL on one machine, NOT encrypted or different physical devices.
No actual plant images, farm locations, or live farmer records are used.
"""
from __future__ import annotations

import argparse
import copy
import json
import random
from dataclasses import dataclass

import torch
from torch import nn

FEATURE_NAMES = (
    "yellow_fraction",
    "brown_fraction",
    "mean_hue",
    "texture_variance",
    "edge_density",
)
CLIENT_NAMES = ("greenhouse_a", "greenhouse_b", "greenhouse_c")


class LeafRiskMLP(nn.Module):
    """A demonstrator predicting a SYNTHETIC binary risk label from five features."""

    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(5, 64), nn.ReLU(),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, 16), nn.ReLU(),
            nn.Linear(16, 1),  # logits; BCEWithLogitsLoss handles sigmoid
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features).squeeze(-1)


@dataclass
class Client:
    name: str
    features: torch.Tensor
    labels: torch.Tensor
    consent: bool = False


def _generate_samples(count: int, shift: float, generator: torch.Generator):
    """Fabricated observations and labels for *software validation only*."""
    raw = torch.rand((count, 5), generator=generator)
    raw[:, 0] = (raw[:, 0] * 0.7 + shift).clamp(0, 1)
    raw[:, 1] = (raw[:, 1] * 0.8 + shift / 2).clamp(0, 1)
    # Mean hue is represented as a normalized [0, 1] value in this demo.
    noise = 0.18 * torch.randn(count, generator=generator)
    score = (2.0 * raw[:, 0] + 1.6 * raw[:, 1]
             - 0.8 * raw[:, 2] + 0.7 * raw[:, 3]
             + 0.4 * raw[:, 4] + noise - 1.55)
    labels = (score > 0).float()
    return raw, labels


def make_demo_data(samples_per_client: int = 120, seed: int = 42):
    """Return distinct synthetic client datasets and an independent holdout."""
    if not 20 <= samples_per_client <= 400:
        raise ValueError("samples_per_client must be between 20 and 400")
    generator = torch.Generator().manual_seed(seed)
    clients = []
    for name, shift in zip(CLIENT_NAMES, (0.00, 0.12, 0.24)):
        x, y = _generate_samples(samples_per_client, shift, generator)
        clients.append(Client(name=name, features=x, labels=y))
    x_val, y_val = _generate_samples(240, 0.08, generator)
    return clients, (x_val, y_val)


def train_local(model: LeafRiskMLP, client: Client, epochs: int = 2,
                lr: float = 0.01) -> float:
    if not client.consent:
        raise PermissionError(f"{client.name} has not opted in to training")
    if not 1 <= epochs <= 3:
        raise ValueError("epochs must be between 1 and 3")
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    objective = nn.BCEWithLogitsLoss()
    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = objective(model(client.features), client.labels)
        loss.backward()
        optimizer.step()
    return round(loss.item(), 6)


def fedavg(models: list[LeafRiskMLP], weights: list[int]) -> dict:
    """Weighted parameter averaging by each participating client's sample count."""
    if not models or len(models) != len(weights) or any(w <= 0 for w in weights):
        raise ValueError("models and positive sample counts are required")
    total = sum(weights)
    averaged = {}
    for key in models[0].state_dict():
        averaged[key] = sum(
            model.state_dict()[key].detach().clone() * (n / total)
            for model, n in zip(models, weights)
        )
    return averaged


def evaluate(model: LeafRiskMLP, data: tuple[torch.Tensor, torch.Tensor]):
    x, y = data
    model.eval()
    with torch.no_grad():
        logits = model(x)
        loss = nn.BCEWithLogitsLoss()(logits, y).item()
        predictions = (torch.sigmoid(logits) >= 0.5).float()
        tp = ((predictions == 1) & (y == 1)).sum().item()
        tn = ((predictions == 0) & (y == 0)).sum().item()
        fp = ((predictions == 1) & (y == 0)).sum().item()
        fn = ((predictions == 0) & (y == 1)).sum().item()
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "validation_loss": round(loss, 5),
        "accuracy": round((tp + tn) / len(y), 5),
        "precision": round(precision, 5),
        "recall": round(recall, 5),
        "f1": round(2 * precision * recall / (precision + recall), 5)
              if precision + recall else 0.0,
    }


def run_demo(*, consent: dict[str, bool] | None = None, rounds: int = 10,
             local_epochs: int = 2, samples_per_client: int = 120,
             seed: int = 42):
    """Simulate consent-gated FL; no raw examples are sent to an aggregator.

    consent must explicitly opt each client in; omission means all disabled.
    All computation is in-process on synthetic data, on the same machine.
    """
    if not 1 <= rounds <= 20:
        raise ValueError("rounds must be between 1 and 20")
    if not 1 <= local_epochs <= 3:
        raise ValueError("local_epochs must be between 1 and 3")
    torch.manual_seed(seed)
    random.seed(seed)
    clients, holdout = make_demo_data(samples_per_client, seed)
    consent = consent or {}
    for client in clients:
        client.consent = consent.get(client.name) is True
    active = [c for c in clients if c.consent]
    if not active:
        raise PermissionError("No opted-in synthetic clients; training blocked")

    global_model = LeafRiskMLP()
    initial_state = copy.deepcopy(global_model.state_dict())
    history = []
    for round_id in range(1, rounds + 1):
        local_models, weights, losses = [], [], []
        for client in active:
            local_model = LeafRiskMLP()
            local_model.load_state_dict(copy.deepcopy(global_model.state_dict()))
            losses.append(train_local(local_model, client, local_epochs))
            local_models.append(local_model)
            weights.append(len(client.labels))
        global_model.load_state_dict(fedavg(local_models, weights))
        history.append({"round": round_id,
                        "training_loss": round(sum(a * w for a, w in zip(losses, weights)) / sum(weights), 5),
                        **evaluate(global_model, holdout)})

    # Fair comparison: one local client, same initial weights, and same total
    # number of epoch passes as one participating FL client across all rounds.
    local_model = LeafRiskMLP()
    local_model.load_state_dict(initial_state)
    local_client = active[0]
    for _ in range(rounds):
        train_local(local_model, local_client, local_epochs)

    return {
        "dataset": "SYNTHETIC - not plant disease ground truth",
        "simulation": "Three simulated clients on one machine; no differential privacy or secure aggregation",
        "features": list(FEATURE_NAMES),
        "participating_clients": [c.name for c in active],
        "excluded_clients": [c.name for c in clients if not c.consent],
        "rounds": rounds,
        "local_epochs": local_epochs,
        "samples_per_client": samples_per_client,
        "holdout_samples": len(holdout[1]),
        "history": history,
        "federated_final": history[-1],
        "local_only_baseline": evaluate(local_model, holdout),
        "privacy": "Only model parameters and sample counts go to FedAvg within this local simulation; model updates may leak information in real deployments.",
    }


def main():
    parser = argparse.ArgumentParser(description="SCD synthetic federated-learning demo")
    parser.add_argument("--demo-consent", action="store_true",
                        help="Explicitly opt all three SIMULATED clients in")
    parser.add_argument("--rounds", type=int, default=10)
    args = parser.parse_args()
    consent = {name: True for name in CLIENT_NAMES} if args.demo_consent else {}
    try:
        print(json.dumps(run_demo(consent=consent, rounds=args.rounds), indent=2))
    except (PermissionError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
