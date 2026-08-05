from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FormKind = Literal["complaint", "suggestion", "bug"]


@dataclass(frozen=True)
class FormField:
    key: str
    required: bool
    prompt_en: str
    prompt_ar: str


@dataclass(frozen=True)
class FormDefinition:
    kind: FormKind
    title_en: str
    title_ar: str
    fields: tuple[FormField, ...]


COMPLAINT_FORM = FormDefinition(
    kind="complaint",
    title_en="Complaint",
    title_ar="Complaint",
    fields=(
        FormField(
            key="target_name",
            required=True,
            prompt_en="Send the name of the reported person.",
            prompt_ar="ابعت اسم المشكو عليه.",
        ),
        FormField(
            key="time_occurred",
            required=True,
            prompt_en="Send the time the issue happened.",
            prompt_ar="ابعت زمن حدوث المشكلة.",
        ),
        FormField(
            key="location",
            required=True,
            prompt_en="Send where the issue happened.",
            prompt_ar="ابعت أين حدثت المشكلة.",
        ),
        FormField(
            key="content",
            required=True,
            prompt_en="Send the complaint details.",
            prompt_ar="ابعت محتوى الشكوى.",
        ),
        FormField(
            key="screenshot",
            required=False,
            prompt_en="Send a screenshot or type skip.",
            prompt_ar="ابعت سكرين شوت للمشكلة أو اكتب تخطي.",
        ),
    ),
)

SUGGESTION_FORM = FormDefinition(
    kind="suggestion",
    title_en="Suggestion",
    title_ar="Suggestion",
    fields=(
        FormField(
            key="name",
            required=True,
            prompt_en="Send your name.",
            prompt_ar="ابعت اسمك.",
        ),
        FormField(
            key="age",
            required=True,
            prompt_en="Send your age.",
            prompt_ar="ابعت عمرك.",
        ),
        FormField(
            key="content",
            required=True,
            prompt_en="Send the suggestion details.",
            prompt_ar="ابعت محتوى الاقتراح.",
        ),
    ),
)

BUG_FORM = FormDefinition(
    kind="bug",
    title_en="Bug Report",
    title_ar="Bug Report",
    fields=(
        FormField(
            key="name",
            required=True,
            prompt_en="Send your name.",
            prompt_ar="ابعت اسمك.",
        ),
        FormField(
            key="location",
            required=True,
            prompt_en="Send where the issue happened.",
            prompt_ar="ابعت أين حدثت المشكلة.",
        ),
        FormField(
            key="reproduction_steps",
            required=True,
            prompt_en="Send how to reproduce the issue.",
            prompt_ar="ابعت كيف يمكننا تكرار المشكلة.",
        ),
        FormField(
            key="screenshot",
            required=True,
            prompt_en="Send a screenshot of the issue.",
            prompt_ar="ابعت سكرين شوت للمشكلة.",
        ),
    ),
)

FORMS: dict[FormKind, FormDefinition] = {
    "complaint": COMPLAINT_FORM,
    "suggestion": SUGGESTION_FORM,
    "bug": BUG_FORM,
}


def get_form(kind: FormKind) -> FormDefinition:
    return FORMS[kind]
