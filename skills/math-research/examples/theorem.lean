import Mathlib

theorem bundled_square_nonnegative (x : ℝ) : 0 ≤ x ^ 2 := by
  exact sq_nonneg x

#print axioms bundled_square_nonnegative
