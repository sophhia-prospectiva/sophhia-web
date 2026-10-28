# P001-CWS-001 — Control de coherencia del árbol web de SOPHHIA 29-N

**Propuesta de anexo operativo a P001/P001-E001.** No sustituye ni modifica el Contrato Prospectivo CP-29N-F0 ni autoriza por sí solo publicaciones. Vigencia sujeta a validación IH específica.

## Objeto
Antes de cada subida de la actualización diaria (habitualmente alrededor de las 10:00 hora peninsular), comprobar que un mismo registro vigente gobierna portada, Dashboard, Bitácora, Explorador y ficheros de datos. Diferenciar siempre día de consulta, fecha de corte de la evidencia, fecha de entrada y fecha de referencia paramétrica del Explorador.

## Secuencia propuesta
1. Ejecutar P001: fuentes, corte temporal y revisión de señales; registrar reservas temporales.
2. Registrar el resultado de IH (pendiente/provisional/definitiva) y su identificador en `data/current.json`; actualizar `data/dashboard.json` y `data/diario_index.json` sin recalibración no autorizada.
3. Preparar la entrada HTML D-00n y actualizar las páginas consumidoras, preservando íntegramente los históricos anteriores.
4. Ejecutar localmente desde la raíz del repositorio: `python3 sophhia-29n/control/verificar_sincronizacion_p001.py` (Python 3, biblioteca estándar).
5. Si indica **STOP PUBLICACIÓN**, corregir las incidencias antes del commit. Si indica **GO TÉCNICO CON RESERVAS**, documentar y someter avisos a IH. El GO técnico nunca equivale a validación IH.
6. Verificar en Safari: portada/`#hoy`, Dashboard, Bitácora y Explorador; fecha del cono, cuadrícula, cuatro paletas, seis deslizadores y visualización móvil. Comprobar enlace a última entrada.
7. Subir a `sophhia-prospectiva/sophhia-web`, rama `main`, bajo la carpeta `sophhia-29n` exclusivamente. Confirmar rutas antes del commit; comprobar Action Pages y acceso público.
8. Conservar comprobantes de fuentes/corte, decisión IH, control técnico, commit SHA, despliegue y prueba visual en el expediente.

## Alcance del verificador
Control local **solo lectura**: identidad/fecha/corte/huso/decisión de la entrada; coherencia de current/dashboard/diario_index; archivos y enlaces; existencia de consulta a current en portada y Explorador; rótulo temporal del cono y retícula; alerta de reservas documentales. No pretende certificar operaciones matemáticas, veracidad de fuentes, funcionamiento JavaScript en navegador ni corrección cromática.

## Salvaguardas
No convertir una aprobación provisional en definitiva. No alterar fechas de entradas archivadas. No sustituir la fecha base del Explorador por la fecha del análisis; ambas deben estar explícitamente diferenciadas. No subir un paquete que contenga rutas fuera de `sophhia-29n`.

**Estado:** texto propuesto para integración al expediente P001, pendiente de aprobación específica del protocolo complementario.
