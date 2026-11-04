"""Brazil is the default country; an explicit international prefix is preserved."""

import re


def normalize_phone(value: str) -> str:
    phone = re.sub(r"[\s().-]", "", value.strip())
    if not phone.startswith("+"):
        if re.fullmatch(r"[0-9]{10,11}", phone):
            phone = "+55" + phone
        elif re.fullmatch(r"55[0-9]{10,11}", phone):
            phone = "+" + phone
    if not re.fullmatch(r"\+[1-9][0-9]{7,14}", phone):
        raise ValueError(
            "Informe DDD e número para Brasil (+55 automático). Para outro país, informe + e o código internacional."
        )
    return phone
