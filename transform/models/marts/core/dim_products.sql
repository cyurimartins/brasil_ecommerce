-- Granularidade: 1 linha por produto.

with

products as (

    select * from {{ ref('stg_olist__products') }}

),

translations as (

    select * from {{ ref('stg_olist__product_category_translation') }}

),

final as (

    select
        products.product_id,
        coalesce(products.product_category_name, 'sem_categoria') as category_name,
        -- 2 categorias não têm tradução na origem: cai para o nome em português.
        coalesce(
            translations.product_category_name_english,
            products.product_category_name,
            'uncategorized'
        ) as category_name_english,
        products.product_name_length,
        products.product_description_length,
        products.product_photos_qty,
        products.product_weight_g,
        products.product_length_cm,
        products.product_height_cm,
        products.product_width_cm,
        products.product_length_cm
        * products.product_height_cm
        * products.product_width_cm as product_volume_cm3

    from products
    left join translations
        on products.product_category_name = translations.product_category_name

)

select * from final
