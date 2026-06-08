# Internet Scan Notes

Scanned on 2026-06-08 for reusable inventory systems, docs, data models, and forecasting approaches.

## Practical Recommendation

Keep this repo as a lightweight proof harness and borrow patterns from mature systems. Do not adopt a full ERP as the first implementation unless the company already uses one.

Best near-term path:

1. Keep the local SQLite ledger as the canonical proof layer.
2. Add importer adapters later for the company's actual source system.
3. Borrow data-model and workflow ideas from InvenTree and OpenBoxes.
4. Borrow replenishment terminology from Odoo and ERPNext.
5. Add forecasting math only after real consumption data exists.

## Systems Worth Borrowing From

### InvenTree

Source:

- Documentation: https://docs.inventree.org/en/stable/
- GitHub: https://github.com/inventree/InvenTree
- API docs: https://inventree.org/extend/api.html

Useful patterns:

- Parts are core entities.
- Stock can be inspected by part and location.
- Stock locations can be hierarchical.
- Stock history is maintained.
- It has suppliers, purchase orders, sales orders, labels, reports, plugins, REST API, and Python bindings.

Best fit for this project:

- Borrow terminology and data-shape ideas for parts, locations, suppliers, purchase orders, labels, and API adapters.
- Consider InvenTree as a possible future backend if the business needs serial tracking, barcodes, purchase orders, and a mature UI.

Claim boundary:

- InvenTree is a strong reference, but adopting it would add Django deployment/admin complexity. It should not replace the lightweight proof harness unless the business needs justify it.

### OpenBoxes

Source:

- Product site: https://openboxes.com/
- API guide: https://docs.openboxes.com/en/latest/api-guide/
- Stock movement API: https://docs.openboxes.com/en/develop/api-guide/outbound/stockMovement/
- GitHub: https://github.com/openboxes/openboxes

Useful patterns:

- Multi-facility inventory.
- Full audit trail on movements.
- Lot tracking and expiry alerts.
- Reorder point calculations.
- Consumption reports and demand forecasting.
- REST APIs for stock movements.

Best fit for this project:

- Borrow the stock movement model: origin, destination, requester, line items, status, requested quantities, and stable identifiers.
- Add lots/expiry only if the business has perishable, regulated, batch, or recall-sensitive inventory.
- Use OpenBoxes as the reference for serious warehouse/healthcare-style discipline.

Claim boundary:

- OpenBoxes is a larger supply-chain system. It may be better as a replacement platform than a dependency for a small first proof.

### Odoo Inventory

Source:

- Reordering rules docs: https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/management/products/reordering_rules.html
- Routes docs: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/use_routes.html

Useful patterns:

- Reordering rules use min quantity, max quantity, and optional multiple quantity.
- Replenishment can be manual or automatic.
- Buy/manufacture routes determine what action is created.
- Forecasted stock and visibility days matter when deciding whether to replenish.

Best fit for this project:

- Add `min_quantity`, `max_quantity`, `order_multiple`, `preferred_vendor`, and `replenishment_route` concepts.
- Keep route logic simple at first: `buy`, `transfer`, `manufacture`, or `manual`.

Claim boundary:

- Odoo replenishment is powerful but can become opaque. Our proof rules require every recommendation to show the exact inputs used.

### ERPNext

Source:

- Documentation home: https://docs.erpnext.com/
- Developer API entry: https://docs.erpnext.com/index

Useful patterns:

- ERPNext covers order management, inventory control, manufacturing, assets, and developer APIs.
- It is useful as an integration target if the company already runs ERPNext.

Best fit for this project:

- Borrow the idea of item-level and warehouse-level reorder levels.
- If the company uses ERPNext, build an adapter that reads item/warehouse stock and writes source references into our ledger.

Claim boundary:

- ERPNext is a full ERP. Do not introduce it unless the company already has it or explicitly wants a broader ERP rollout.

### supplychainpy

Source:

- Documentation/site: https://www.supplychainpy.org/

Useful patterns:

- Demand planning, reorder levels, safety-stock analysis, and inventory simulation.

Best fit for this project:

- Use as a forecasting reference after the pilot captures enough consumption data.
- Do not add as a dependency until real demand history exists and a measurable forecasting need is proven.

## Concepts To Add To Our Backlog

High priority:

- Locations table and location-aware stock.
- Suppliers table.
- Purchase-order recommendation export.
- Reorder policy fields: min quantity, max quantity, order multiple.
- Demand-source field: manual, calendar, sales, production, external import.
- Evidence fields on every recommendation.

Medium priority:

- Lots/batches and expiry dates.
- Barcode/label generation.
- Cycle-count queue based on risk.
- Import idempotency table for source-system records.
- Exception dashboard for unknown, stale, or conflicting data.

Later:

- Forecasting beyond rolling average.
- Multi-warehouse transfers.
- Vendor lead-time performance tracking.
- Integration adapters for InvenTree, OpenBoxes, Odoo, ERPNext, spreadsheets, or POS systems.

## Proof-Outcome Guardrail

Do not copy public marketing claims from these systems into our project. Treat them as design references only. Our claims must be based on our local tests, source-system parity checks, and the company's pilot evidence.

