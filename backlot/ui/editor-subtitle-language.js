// Legacy means no explicit declaration; do not silently label or migrate it.
export function languageSelection(style){return style.language??'legacy';}
export function languageParams(value,supported=true){return supported&&value!=='legacy'?{language:value}:{};}
