class ExpenseController:
    def __init__(self, db_manager):
        self.db = db_manager

    def add_expense(self, amount_str, category, date_str, notes, is_fixed, is_usd, payment_method_label, selected_tag_ids):
        # 1. Validación de monto
        amount_clean = amount_str.replace(",", "").replace(".", "").strip()
        if not amount_clean:
            return False, "El monto no puede estar vacío."
            
        try:
            # En COP normalmente son enteros grandes, en USD pueden tener decimales
            if is_usd:
                amount = float(amount_clean)
            else:
                amount = int(amount_clean)
                
            if amount <= 0:
                return False, "El monto debe ser mayor a cero."
        except ValueError:
            return False, "Por favor, ingresa un monto numérico válido."

        # 2. Mapeo de método de pago
        pm_code = "DEBIT"
        if "Tarjeta" in payment_method_label or "TC" in payment_method_label:
            pm_code = "CREDIT_CARD"
        elif "Efectivo" in payment_method_label:
            pm_code = "CASH"

        # 3. Lógica de Negocio y Base de Datos
        try:
            if not is_usd:
                # Verificación de fondos (Business Logic)
                current_bal = self.db.get_cop_balance()
                if pm_code != "CREDIT_CARD" and amount > current_bal:
                    # En la vida real, el controlador podría devolver un código de estado especial
                    # para mostrar un diálogo de confirmación (BalanceWarningDialog), pero por ahora 
                    # asumiremos que pasa o devuelve un warning.
                    pass # Dejaremos la lógica de warning al View por ahora o la adaptamos luego

                tx_id = self.db.add_cop_expense(date_str, category, amount, is_fixed=is_fixed, payment_method=pm_code, notes=notes)
                if selected_tag_ids:
                    self.db.set_tags_for_record("cop_transactions", tx_id, selected_tag_ids)
                return True, "Gasto COP registrado con éxito."
            else:
                tx_id = self.db.add_usd_expense(date_str, category, amount, notes=notes)
                if selected_tag_ids:
                    self.db.set_tags_for_record("usd_transactions", tx_id, selected_tag_ids)
                return True, "Gasto USD registrado con éxito."
        except Exception as e:
            return False, f"Error interno: {str(e)}"

    def get_balances(self):
        return {
            "cop": self.db.get_cop_balance(),
            "usd": self.db.get_usd_balance()
        }

    def get_categories(self, is_usd_or_type):
        if isinstance(is_usd_or_type, bool):
            cat_type = "EXPENSE_USD" if is_usd_or_type else "EXPENSE_COP"
        else:
            cat_type = "EXPENSE_USD" if "USD" in str(is_usd_or_type) else "EXPENSE_COP"
        return [c["name"] for c in self.db.get_categories(cat_type)]

    def get_checklist(self, checklist_ym):
        return self.db.get_recurring_checklist_status(checklist_ym)

    def get_expenses(self, limit, currency_filter, payment_method_label):
        # Mapear filtros
        curr_filter = None
        if currency_filter == "COP": curr_filter = "COP"
        elif currency_filter == "USD": curr_filter = "USD"

        pm_code = None
        if payment_method_label:
            if "Débito" in payment_method_label: pm_code = "DEBIT"
            elif "TC" in payment_method_label: pm_code = "CREDIT_CARD"

        return self.db.get_all_expenses(limit=limit, currency_filter=curr_filter, payment_method=pm_code)

    def pay_recurring(self, item_id, date_str, target_month):
        success, msg, warn_data = self.db.pay_recurring_item(item_id, date_str=date_str, target_month=target_month)
        return success, msg, warn_data

    def unpay_recurring(self, tx_id, currency):
        return self.db.unpay_recurring_item(tx_id, currency=currency)

    def delete_expense(self, record_id, source_table_or_currency, force=False):
        if source_table_or_currency in ("usd_transactions", "USD"):
            return self.db.delete_usd_transaction(record_id, force=force)
        else:
            return self.db.delete_cop_transaction(record_id, force=force)

