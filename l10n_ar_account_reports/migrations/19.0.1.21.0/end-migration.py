import logging

_logger = logging.getLogger(__name__)

# En 18.0 estos dos modulos existian; en 19.0 su contenido se absorbio
# (account_tax_settlement -> account_accountant_ux,
#  l10n_ar_account_tax_settlement -> l10n_ar_account_reports).
# En produccion ya estan desinstalados, pero en bases mas viejas (stage) siguen
# instalados y quedan colgados con data que ya no tiene modulo en el addons path.
#
# Corre como end- (no pre-) a proposito: el pre-migration 19.0.1.20.0 reapunta los
# xml_id de inflation.adjustment.index desde l10n_ar_account_tax_settlement hacia
# este modulo. remove_module borra TODO lo que el modulo viejo todavia posee via
# ir_model_data, asi que tiene que correr despues de ese reapuntado y despues de
# que este modulo haya cargado su propia data.
MODULES_TO_REMOVE = (
    "account_tax_settlement",
    "l10n_ar_account_tax_settlement",
)


def migrate(cr, version):
    """Elimina los modulos absorbidos que quedaron instalados. Idempotente."""
    try:
        from odoo.upgrade import util
    except ImportError:
        # odoo.upgrade solo existe en builds del upgrade platform. En un build
        # normal / -u a mano no esta, y no queremos romper la actualizacion.
        _logger.warning(
            "l10n_ar_account_reports: odoo.upgrade no disponible, se omite la remocion de %s",
            ", ".join(MODULES_TO_REMOVE),
        )
        return

    for module in MODULES_TO_REMOVE:
        cr.execute("SELECT state FROM ir_module_module WHERE name = %s", (module,))
        row = cr.fetchone()
        if not row:
            _logger.info("l10n_ar_account_reports: %s no esta en la base, nada que hacer", module)
            continue
        _logger.info("l10n_ar_account_reports: eliminando modulo %s (estado %s)", module, row[0])
        util.remove_module(cr, module)
