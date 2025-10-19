FROM php:8.3-apache
RUN a2enmod rewrite \
 && docker-php-ext-install pdo pdo_mysql
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
WORKDIR /var/www
COPY composer.json /var/www/composer.json
RUN composer install --no-interaction --prefer-dist || true
COPY src/ /var/www/src/
COPY sql/ /var/www/sql/
COPY scripts/ /var/www/scripts/
COPY public/ /var/www/html/
ENV APACHE_DOCUMENT_ROOT=/var/www/html
# Enable .htaccess overrides
RUN sed -ri -e 's!/var/www/html!/var/www/html!g' /etc/apache2/sites-available/000-default.conf \
 && sed -ri -e 's/AllowOverride None/AllowOverride All/g' /etc/apache2/apache2.conf
