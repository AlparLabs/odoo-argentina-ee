"""[AlparData] Conserva las etiquetas viejas de l10n_ar_ux que quedaron en uso.

l10n_ar_ux 19 ya no define estas etiquetas. Su pre-migración 19.0.1.6.0 les
saca el xmlid si están en uso, para que la limpieza final no las borre. Pero
al migrar salteando versiones, l10n_ar_tax se instala y su post_init_hook
(_add_wh_taxes) vincula tax_tag_a_cuenta_iibb a las líneas de impuestos de
IIBB después de esa pre-migración: la limpieza intentaba borrar la etiqueta y
fallaba por la FK de account_account_tag_account_tax_repartition_line_rel.

Corre como post de l10n_ar_account_reports, que depende de l10n_ar_tax, así
que siempre es después del hook y antes de la limpieza. Repite el criterio de
ADHOC: etiqueta en uso -> se le saca el xmlid y queda como dato.
"""
import logging

_logger = logging.getLogger(__name__)

# Misma lista que l10n_ar_ux/migrations/19.0.1.6.0/pre-migration.py
UX_TAGS = [
    "tag_a_cuenta_ganancias",
    "tag_a_cuenta_iva",
    "tag_iva_primer_parrafo",
    "tag_unaffected_earnings",
    "tag_impuestos_a_las_ganancias",
    "tag_liquidacion_de_iva",
    "tag_liquidacion_de_iibb",
    "tag_liquidacion_de_ganancias",
    "tag_liquidacion_sicore_aplicado",
    "tag_liquidacion_iibb_aplicado",
    "tax_tag_a_cuenta_suss",
    "tax_tag_a_cuenta_iibb",
    "tax_tag_a_cuenta_ganancias",
    "tax_tag_a_cuenta_iva",
    "tag_ret_perc_iibb_aplicada",
    "tag_ret_perc_sicore_aplicada",
]


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        DELETE FROM ir_model_data d
         WHERE d.module = 'l10n_ar_ux'
           AND d.model = 'account.account.tag'
           AND d.name IN %s
           AND (
                EXISTS (SELECT 1 FROM account_account_tag_account_tax_repartition_line_rel r
                         WHERE r.account_account_tag_id = d.res_id)
             OR EXISTS (SELECT 1 FROM account_account_tag_account_move_line_rel r
                         WHERE r.account_account_tag_id = d.res_id)
             OR EXISTS (SELECT 1 FROM account_account_account_tag r
                         WHERE r.account_account_tag_id = d.res_id)
           )
        RETURNING d.name
        """,
        [tuple(UX_TAGS)],
    )
    kept = sorted(row[0] for row in cr.fetchall())
    if kept:
        _logger.info("l10n_ar_ux: etiquetas en uso que se conservan sin xmlid: %s", kept)
