import logging

_logger = logging.getLogger(__name__)

# En 18.0 el modelo inflation.adjustment.index, sus vistas y sus acciones vivian en
# l10n_ar_account_tax_settlement. En 19.0 ese modulo desaparecio y su contenido se
# absorbio en l10n_ar_account_reports reutilizando los mismos nombres de xml_id
# (167 de 169). Los registros siguen en la base apuntando al modulo viejo, asi que
# al cargar data/inflation_adjustment_index.xml Odoo no los reconoce, intenta
# crearlos de nuevo y salta la constraint del modelo:
#   An index already exists for period January 2013
OLD_MODULE = "l10n_ar_account_tax_settlement"
NEW_MODULE = "l10n_ar_account_reports"


def migrate(cr, version):
    """Reapunta al modulo nuevo los xml_id del modulo absorbido."""
    cr.execute(
        """
        UPDATE ir_model_data d
           SET module = %s
         WHERE d.module = %s
           AND NOT EXISTS (
                 SELECT 1
                   FROM ir_model_data e
                  WHERE e.module = %s
                    AND e.name = d.name
               )
     RETURNING d.model
        """,
        (NEW_MODULE, OLD_MODULE, NEW_MODULE),
    )
    movidos = [row[0] for row in cr.fetchall()]
    if not movidos:
        _logger.info("%s: no hay xml_id de %s para reapuntar", NEW_MODULE, OLD_MODULE)
        return

    conteo = {}
    for modelo in movidos:
        conteo[modelo] = conteo.get(modelo, 0) + 1
    for modelo, cantidad in sorted(conteo.items()):
        _logger.info("%s: %s xml_id reapuntados desde %s (%s)", NEW_MODULE, cantidad, OLD_MODULE, modelo)

    # los que quedaron son colisiones de nombre: el modulo nuevo ya tiene ese xml_id
    cr.execute("SELECT name, model FROM ir_model_data WHERE module = %s", (OLD_MODULE,))
    restantes = cr.fetchall()
    if restantes:
        _logger.warning(
            "%s: quedaron %s xml_id en %s por colision de nombre: %s",
            NEW_MODULE,
            len(restantes),
            OLD_MODULE,
            ", ".join("%s (%s)" % (n, m) for n, m in restantes),
        )
