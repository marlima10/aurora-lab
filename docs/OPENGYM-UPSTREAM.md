# Sugestões para o openGym oficial

Rascunhos para envio separado ao projeto openGym. A observação foi feita em modo demonstração no commit upstream 2d70e026, com interface em pt-BR.

## 1. Distinguish weekday labels in Brazilian Portuguese

**Observed:** In Home and Plan, the pt-BR weekday abbreviations render as S T Q Q S S D. Wednesday and Thursday share Q, and Monday, Friday and Saturday share S. The messages near the weekday abbreviations in frontend/src/locales/pt-BR.js cause the ambiguity.

**Proposed:** Use Seg, Ter, Qua, Qui, Sex, Sáb and Dom. If the layout needs shorter labels, use distinct two-letter forms. Keep accessible full weekday names and verify both views at 390 px.

## 2. Avoid redundant bilingual exercise labels

**Observed:** Some translated names repeat the original exercise in parentheses, for example “Leg Press 45 Graus No Sled (Sled 45° Leg Press)”. This makes short lists harder to scan.

**Proposed:** Display only the localized name where it uniquely identifies the exercise. Keep the original as a search alias and reserve it as a disambiguator for names that would otherwise collide. Verify pt-BR search using either wording.

## 3. Compact rest days in the Plan view

**Observed:** Each rest day occupies the same vertical space as a day with a workout, which makes sparse plans harder to scan on phones.

**Proposed:** Render rest days as compact rows with a visible weekday and rest label. Preserve the edit action, keyboard focus and touch target. Compare sparse and full plans on mobile.