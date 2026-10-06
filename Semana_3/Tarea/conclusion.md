# Conclusión — Campaña de reactivación Starbucks Rewards (cupón de $5)

**Para:** Presidente de Marketing
**Asunto:** A quién enviar el cupón de $5 y cuánto vale la decisión

## Recomendación

**Contactar únicamente al 20% de la base con mayor uplift estimado** (≈ 8,000 de 40,000 clientes), ordenados con el modelo de uplift T-learner con Random Forest. No enviar la campaña a toda la base ni al segmento de "mayor riesgo de abandono".

## Por qué: las tres políticas comparadas

Medido sobre 12,000 clientes de prueba que el modelo nunca vio, usando el experimento aleatorio (tratamiento vs. control) como juez:

| Política | Valor neto en prueba | Estimado en la base completa (×3.3) |
|---|---|---|
| Contactar a todos | **−$20,236** (−$1.69 por cliente) | ≈ −$67,000 |
| Top 30% por riesgo de churn | +$245 (+$0.07 por cliente) | ≈ +$800 |
| **Top 20% por uplift (Random Forest)** | **+$4,434** (+$1.85 por cliente) | **≈ +$14,800** |

- **Contactar a todos destruye valor.** El efecto promedio de la campaña es positivo, pero casi la mitad de la base son *Sure Things* (iban a comprar igual y les regalamos $5) y 7% son *Sleeping Dogs* (el contacto los espanta).
- **Targetear por riesgo de churn no funciona.** El 71% de ese grupo son *Lost Causes*: clientes que se van con o sin cupón. Saber quién se va no dice a quién podemos retener.
- **El 20% es el punto donde el último cliente contactado todavía deja dinero.** Antes de ese punto cada cliente aporta; a partir del 40% cada cliente adicional resta. Entre 15% y 25% el valor total es prácticamente igual, por lo que el 20% es una cifra robusta, no un óptimo frágil. El valor *por cliente* es máximo al 10%, pero eso deja dinero sobre la mesa en el total.

## Qué tan cerca estuvo el modelo de la verdad

El dataset incluía el tipo real de cada cliente (información que en la operación nunca existe), lo que permitió auditar el modelo:

| Modelo dentro del T-learner | Correlación con el uplift real | Qini |
|---|---|---|
| Logística (base) | 0.619 | +0.142 |
| Árbol sin límite | 0.204 | +0.066 |
| Árbol max_depth=2 | 0.605 | +0.112 |
| Árbol max_depth=5, min_samples_leaf=200 | 0.753 | +0.152 |
| **Random Forest (max_depth=6, min_samples_leaf=100)** | **0.857** | **+0.157** |
| Gradient Boosting (max_depth=3, lr=0.05) | 0.848 | +0.156 |
| *Referencia: modelo de riesgo/churn* | *0.227* | *+0.048* |

- Con el modelo base, **el top 20% elegido fue 80% Persuadables** (contra 22% en la base general): el presupuesto se concentra donde la campaña sí causa la compra.
- El modelo Random Forest **casi duplica el valor** de la logística (+$4,434 vs. +$2,369 en prueba) con la misma recomendación de 20%.
- **Limitación:** el modelo logístico no detecta bien a los Sleeping Dogs (les estima un efecto positivo cuando el real es negativo). Los modelos de árboles mejoran ese punto, pero ninguno es perfecto; el árbol sin restricciones sobreajusta y pierde dinero.

## Siguientes pasos

1. Lanzar al 20% con mayor uplift, **manteniendo un grupo de control aleatorio** para medir el resultado real (sin control no sabremos si funcionó).
2. Reentrenar el modelo con cada nueva campaña; el uplift cambia con la oferta y la temporada.
3. Compensar a los clientes leales (Sure Things) con beneficios del programa de lealtad, no con cupones, para no erosionar margen ni la percepción de justicia.
