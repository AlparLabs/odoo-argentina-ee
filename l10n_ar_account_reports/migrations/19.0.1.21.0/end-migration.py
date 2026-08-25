import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# En 18.0 estos dos modulos existian; en 19.0 su contenido se absorbio
# (account_tax_settlement -> account_accountant_ux,
#  l10n_ar_account_tax_settlement -> l10n_ar_account_reports).
# En produccion ya estan desinstalados, pero en bases mas viejas (stage) siguen
# instalados y su codigo ya no esta en el addons path, lo que deja el build con:
#   Some modules have inconsistent states, some dependencies may be missing
#
# Corre como end- (no pre-) a proposito: el pre-migration 19.0.1.20.0 reapunta los
# xml_id de inflation.adjustment.index desde l10n_ar_account_tax_settlement hacia
# este modulo. La desinstalacion borra lo que el modulo viejo todavia posee via
# ir_model_data, asi que tiene que correr despues de ese reapuntado y despues de
# que este modulo haya cargado su propia data.
MODULES_TO_REMOVE = (
    "account_tax_settlement",
    "l10n_ar_account_tax_settlement",
)

UNINSTALLABLE_STATES = ("installed", "to upgrade", "to install", "to remove")


def migrate(cr, version):
    """Desinstala los modulos absorbidos que quedaron colgados. Idempotente."""
    cr.execute(
        "SELECT name, state FROM ir_module_module WHERE name IN %s",
        (MODULES_TO_REMOVE,),
    )
    estados = dict(cr.fetchall())
    pendientes = [name for name, state in estados.items() if state in UNINSTALLABLE_STATES]
    if not pendientes:
        _logger.info(
            "l10n_ar_account_reports: nada que desinstalar, estados actuales: %s",
            estados or "modulos ausentes de la base",
        )
        return

    try:
        from odoo.upgrade import util
    except ImportError:
        util = None

    if util is not None:
        # Camino preferido: requiere odoo_upgrade instalado (requirements.txt).
        for module in pendientes:
            _logger.info("l10n_ar_account_reports: remove_module(%s), estado previo %s", module, estados[module])
            util.remove_module(cr, module)
        return

    # Fallback sin dependencias: el uninstall estandar del ORM. module_uninstall()
    # borra la data del modulo respetando el orden y las constraints, y deja el
    # modulo en 'uninstalled' (mismo estado que ya tiene produccion).
    _logger.warning(
        "l10n_ar_account_reports: odoo.upgrade.util no disponible, se usa module_uninstall() del ORM para %s",
        ", ".join(pendientes),
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    modules = env["ir.module.module"].search([("name", "in", pendientes)])
    modules.module_uninstall()
    env.flush_all()

    cr.execute(
        "SELECT name, state FROM ir_module_module WHERE name IN %s",
        (MODULES_TO_REMOVE,),
    )
    for name, state in cr.fetchall():
        _logger.info("l10n_ar_account_reports: %s quedo en estado %s", name, state)
