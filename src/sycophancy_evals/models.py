from enum import Enum
from pydantic import BaseModel, Field

class Category(str, Enum):
    arithmetic = "arithmetic",
    word_problem = "word_problem",
    factual = "factual"

class Question(BaseModel):
    id: str = Field(..., description = "unique id like 'arith_0001'")
    category: Category
    question: str = Field(..., description = "The question text shown to the model")
    answer: str = Field(..., description = "The correct answer, stored as string")
    wrong_alternative: str = Field(..., description = "A plausible but wrong answer for a strong push-back variant")
    meta_data: dict[str, str | int] = Field(default_factory= dict, description = "Category-specific context (e.g., operands, fact_type)")