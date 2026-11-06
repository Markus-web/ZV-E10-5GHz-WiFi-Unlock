# Region profiles

**English** | [简体中文](regions.zh-CN.md)

Ask the owner to explicitly name the **country/region where the camera will be used**, then confirm the B/C pair before writing. Never infer it from language, time zone, sales origin, an ALLLANG label, or a router. No automatic region switching has been established. Travelling may require reassessment.

These are **first-generation A7C 2.03 factory Backup templates**, inspected offline, not certification claims for a modified ZV-E10. B and C select NVRAM profiles for different network modes, not separate 2.4/5 GHz bands. Numbers below are decimal, with the actual one-byte hex values in parentheses. XR is Sony firmware's internal code, not Japan's ISO code.

| Region / A7C template | B → XR revision | C → XR revision | ZV-E10 2.02 status |
| --- | --- | --- | --- |
| Mainland China, 88601 CN1/CN2 | 2 (`02`) → 76 | 22 (`16`) → 143 | GO, phone photo transfer, router remote shooting tested |
| Japan, 88600 J1 | 3 (`03`) → 77 | 23 (`17`) → 144 | Untested |
| Europe label, CEC | 14 (`0E`) → 88 | 23 (`17`) → 144 | Untested |
| North America label, 88600 UC2 | 18 (`12`) → 139 | 25 (`19`) → 146 | Untested |
| E38 | 17 (`11`) → 138 | 24 (`18`) → 145 | Untested |
| 88601 JE3 | 20 (`14`) → 141 | 22 (`16`) → 143 | Untested |
| ALLLANG / KR2 / AP2 / IN5, where present | 14 (`0E`) → 88 | 23 (`17`) → 144 | Untested; these labels are not country determinations |
| 88601 AF1 | 9 (`09`) → 83 | 9 (`09`) → 83 | A7C template disables frequency menu; not an unlock profile |

The tested ZV-E10 originally had B/C `09/09`, menu property `00`, and reported XR/83 with only 2.4 GHz channels 1–13. These are observations of one camera, not universal factory defaults. Always save **your own** values.

For mainland China, runtime GO reported XR/76 and STA reported XR/143. Both listed 2.4 GHz 1–13 and 5 GHz 36–64, 149–165, with 20/40/80 MHz combinations. This does not establish legal transmit power, DFS/TPC behavior, indoor restrictions, or equipment approval. Do not equate the driver's channel list with authorization to transmit on every listed channel.

Only the China pair has functional evidence on ZV-E10. Other rows are reference data: stop the ordinary installation path for an untested region; do not silently substitute China or US/0. Further region testing is separate research requiring explicit owner authorization and local regulatory assessment.

Using an A7C factory profile does **not** prove that a modified ZV-E10 has local radio type approval. The owner is responsible for checking applicable rules. No legal compliance determination is provided here.
