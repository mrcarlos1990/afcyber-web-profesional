# Propuesta de rutas para AFCyber Préstamos Enterprise

Propuesta del 6 de octubre de 2026. No son páginas publicadas ni rutas implementadas. No se redactaron políticas técnicas para la aplicación.

Las páginas corporativas aprobadas siguen siendo independientes:

- `https://afcybersolutions.com.do/privacy-policy`
- `https://afcybersolutions.com.do/terms-and-conditions`

## Rutas propuestas

| Finalidad | Ruta propuesta | Estado |
| --- | --- | --- |
| Privacidad de la aplicación | `/apps/afcyber-prestamos-enterprise/privacy-policy` | Propuesta; requiere confirmar el funcionamiento de la app y aprobar el contenido. |
| Términos de la aplicación | `/apps/afcyber-prestamos-enterprise/terms-and-conditions` | Propuesta; documento específico separado del sitio corporativo. |
| Soporte de la aplicación | `/apps/afcyber-prestamos-enterprise/support` | Propuesta; puede usar el canal oficial `soporte@afcybersolutions.com.do` cuando se confirme el flujo de atención. |
| Solicitud de eliminación de cuenta/datos | `/apps/afcyber-prestamos-enterprise/data-deletion` | Condicional; no implementar ni prometer eliminación hasta determinar si aplica y cómo se atenderá. |

El prefijo de producto permite incorporar futuras aplicaciones sin mezclar sus documentos. Las rutas, si se aprueban y se crean, deben responder públicamente sin autenticación y conservar una URL estable. No se añaden al menú, sitemap ni Play Console mientras solo sean una propuesta.

## Qué se inspeccionó

Este repositorio es el sitio corporativo de Flask y su versión estática. Contiene contactos, servicios, portafolio, panel administrativo, descargas, solicitudes de servicio y documentos con firma. El login administrativo de la web no demuestra que la aplicación Préstamos Enterprise cree cuentas de usuario.

No se encontraron fuentes de la aplicación móvil, manifiesto Android, identificador de paquete, permisos, dependencias/SDK de la app, flujo de cuentas ni implementación de eliminación de datos. El sistema de documentos y firmas de la web tampoco permite inferir cómo trata datos la aplicación móvil.

## Información necesaria antes de redactar o publicar

Confirmar con la implementación real de Préstamos Enterprise:

- Identificador de paquete, versión y nombre mostrado en Google Play.
- Si hay registro de cuentas de usuario o únicamente uso local/licencias; cómo se vincula la identidad del usuario.
- Datos tratados, finalidad y responsables; si AFCyber recibe o accede a esos datos.
- Dónde se almacena la información y si existen servicios remotos, sincronización o copias de respaldo.
- Permisos del dispositivo y su finalidad; dependencias que puedan recopilar o transmitir información.
- Si existen analítica, reportes de errores o terceros receptores.
- Si corresponde eliminación de cuentas/datos: mecanismo real de solicitud, verificación, alcance, plazos y excepciones confirmadas.
- Condiciones comerciales/licencias y soporte aprobados para este producto.

Estos puntos son preguntas pendientes, no afirmaciones sobre el funcionamiento de la aplicación.

## Criterio de Google Play para la ruta condicional

Google Play exige un mecanismo dentro de la app y un recurso web para solicitar eliminación cuando la app permite crear una cuenta dentro de ella. La página no debe prometer una función que no existe. La aplicabilidad a Préstamos Enterprise sigue pendiente de confirmar; no se infiere a partir de su nombre ni de la autenticación del panel web. Referencia oficial: [requisitos de eliminación de cuentas de Google Play](https://support.google.com/googleplay/android-developer/answer/13327111).
