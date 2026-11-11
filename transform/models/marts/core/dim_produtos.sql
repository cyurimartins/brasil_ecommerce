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
        products.product_id as id_produto,
        coalesce(products.product_category_name, 'sem_categoria') as categoria,
        -- 2 categorias não têm tradução na origem: cai para o nome em português.
        coalesce(
            translations.product_category_name_english,
            products.product_category_name,
            'uncategorized'
        ) as categoria_ingles,
        products.product_name_length as tamanho_nome,
        products.product_description_length as tamanho_descricao,
        products.product_photos_qty as quantidade_fotos,
        products.product_weight_g as peso_g,
        products.product_length_cm as comprimento_cm,
        products.product_height_cm as altura_cm,
        products.product_width_cm as largura_cm,
        products.product_length_cm
        * products.product_height_cm
        * products.product_width_cm as volume_cm3

    from products
    left join translations
        on products.product_category_name = translations.product_category_name

)

select * from final
