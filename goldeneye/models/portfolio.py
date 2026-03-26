"""Domain model: the overall account / portfolio snapshot."""

from dataclasses import dataclass, field

from goldeneye.models.position import Position


@dataclass
class Portfolio:
    cash: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)

    @property
    def equity(self) -> float:
        return self.cash + sum(p.market_value for p in self.positions.values())

    @property
    def unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self.positions.values())
