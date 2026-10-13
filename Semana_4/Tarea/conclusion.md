# Conclusión — Carrusel “Para ti” en la app de la cafetería

**Para:** Presidente de Marketing
**De:** Grupo 9 — Marketing Analytics
**Asunto:** ¿Extendemos el carrusel a toda la base y con qué recomendador?

## Recomendación

1. **Sí, mantener el carrusel y extenderlo a toda la base de 8,000 clientes.** Es la única versión con efecto demostrado, y ese efecto es positivo después de pagar su costo.
2. **No cambiar todavía el recomendador sin probarlo.** El siguiente paso es un experimento de 3 grupos (sin carrusel / popularidad / **filtrado por ítem con respaldo de popularidad**). El recomendador nuevo solo reemplaza al actual si gana en **ingreso incremental**, no en tasa de acierto.

## Lo que demostró el experimento (90 días, 4,000 vs 4,000 clientes asignados al azar)

| Indicador | Resultado |
|---|---|
| ARPU incremental (ingreso) | **+$1.11 por cliente** · IC 95% +$0.37 a +$1.86 |
| Margen neto incremental (después de $0.20 de costo) | **+$0.51 por cliente** · IC 95% +$0.05 a +$0.98 |
| CLV incremental (r = 0.78, d = 0.03 trimestral; factor 3.12) | **+$1.60 por cliente** · ≈ **+$12,800** en los 8,000 clientes |

- El efecto es real (el intervalo no toca el cero), pero **el colchón es estrecho**: en el peor escenario plausible el margen neto apenas cubre el costo.
- **El 31% de lo que se vendió de los productos mostrados se habría vendido de todos modos.** El grupo control compró esos mismos productos sin ver el carrusel. Por eso el efecto real (+$1.11) es mucho menor que el ingreso total de esos productos en los clientes tratados ($1.38).

## Comparación de recomendadores

Tasa de acierto medida solo en clientes que **no** vieron el carrusel:

| Recomendador | Hit rate@3 | Cobertura (de 28) | Ingreso incremental (US$/cliente) |
|---|---|---|---|
| Popularidad (el carrusel actual) | 0.221 | 12 | **+1.11** (medido en el A/B) |
| Filtrado por cliente | 0.301 | 28 | sin medir |
| Filtrado por ítem | 0.401 | 28 | sin medir |
| Híbrido ítem + popularidad (modelo propio) | 0.408 | 28 | sin medir |
| **Ítem + respaldo de popularidad (propuesto)** | **0.410** | **28** | sin medir |

## ¿Un hit rate alto significa ingreso extra?

**No necesariamente, y es el riesgo principal de esta decisión.**
- El recomendador por ítem “acierta” 85% más que la popularidad. Pero un acierto en el control es una compra que **ocurrió sin ninguna recomendación**: el modelo adivinó el gusto del cliente, no lo cambió.
- Justamente porque recomienda lo que más se parece a lo que el cliente ya compra, es probable que una parte mayor de sus aciertos **hubiera ocurrido igual**. Su ventaja en ingreso incremental debería ser menor que su ventaja en hit rate.
- Si se reportara el hit rate como aumento de ventas, **sobreestimaríamos el ARPU**. La prueba es la misma: en los clientes tratados el hit rate de la popularidad sube de 22% a 52% por el simple hecho de mostrar los productos, y aun así el ingreso extra es solo $1.11.

## Por qué el filtrado por ítem es el candidato

- Mejor tasa de acierto (0.41 vs 0.22) y recomienda los 28 productos, no siempre los mismos 12.
- Es barato de operar: una tabla de 29 × 29 que se recalcula una vez por semana. El filtrado por cliente necesita 64 millones de similitudes y acierta menos.
- Es explicable: “porque compraste Té Chai”.
- Resuelve a los clientes nuevos. El 4% sin historial recibe lo más popular, que para ellos acierta el doble que el filtrado por ítem.

## Siguientes pasos

1. **Extender el carrusel actual a toda la base**, manteniendo siempre un **grupo control permanente** (~10%) para seguir midiendo.
2. **Experimento de 3 grupos durante 90 días.** Como el gasto por cliente es muy disperso (desviación de $16.7), conviene ajustar por el gasto previo (CUPED) y medir margen semana a semana para detectar fatiga o efecto novedad.
3. **No mostrar el carrusel a todos por igual a futuro.** Con el grupo control se puede entrenar un modelo de uplift (Semana 3) para mostrarlo solo a los clientes en quienes el ingreso incremental esperado supere el costo de $0.20.

> **Nota:** la validación final contra la información oculta del laboratorio (ingreso incremental verdadero de cada recomendador) queda pendiente. Los archivos todavía no se han publicado. Al tenerlos se completa la columna “Ingreso incremental” y se confirma o corrige la elección.
