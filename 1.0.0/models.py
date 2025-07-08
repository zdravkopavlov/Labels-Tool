from dataclasses import dataclass
from .units import mm_to_px, mm_to_pt

@dataclass(frozen=True)
class SheetTemplate:
    cols: int = 3
    rows: int = 7
    label_w_mm: float = 63.5
    label_h_mm: float = 38.1
    col_gap_mm: float = 3.0
    row_gap_mm: float = 0.0

    def label_rect_px(self, col, row, left_mm, top_mm):
        x0 = mm_to_px(left_mm + col * (self.label_w_mm + self.col_gap_mm))
        y0 = mm_to_px(top_mm + row * (self.label_h_mm + self.row_gap_mm))
        x1 = x0 + mm_to_px(self.label_w_mm)
        y1 = y0 + mm_to_px(self.label_h_mm)
        return x0, y0, x1, y1

    def label_rect_pt(self, col, row, left_mm, top_mm):
        x = mm_to_pt(left_mm + col * (self.label_w_mm + self.col_gap_mm))
        y = mm_to_pt(top_mm + row * (self.label_h_mm + self.row_gap_mm))
        return x, y

@dataclass
class Label:
    name_main: str
    name_sub: str
    price_bgn: str
    price_eur: str
    unit: str
