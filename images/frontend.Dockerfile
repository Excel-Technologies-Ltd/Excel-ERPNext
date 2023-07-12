ARG FRAPPE_VERSION
ARG ERPNEXT_VERSION

FROM frappe/assets-builder:${FRAPPE_VERSION} as assets

WORKDIR /home/frappe/frappe-bench

COPY . apps/excel_erpnext

# RUN bench setup requirements

# RUN bench build --production --verbose --hard-link

RUN install-app excel_erpnext

FROM frappe/erpnext-nginx:${ERPNEXT_VERSION}

COPY --from=assets /out /usr/share/nginx/html
