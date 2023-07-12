ARG ERPNEXT_VERSION
FROM frappe/erpnext-worker:${ERPNEXT_VERSION}

COPY . ../apps/excel_erpnext

USER root

RUN install-app excel_erpnext

USER frappe
