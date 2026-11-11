-- Granularidade: 1 linha por pedido.
-- ~550 pedidos têm mais de uma avaliação; mantemos a mais recente (o cliente pode
-- ter reavaliado), com desempate determinístico para o resultado ser estável.

with

reviews as (

    select * from {{ ref('stg_olist__order_reviews') }}

),

ranked as (

    select
        *,
        count(*) over (partition by order_id) as review_count,
        row_number() over (
            partition by order_id
            order by review_answered_at desc nulls last, review_created_at desc, review_id asc
        ) as recency_rank

    from reviews

),

latest as (

    select
        order_id,
        review_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_created_at,
        review_answered_at,
        review_count

    from ranked
    where recency_rank = 1

)

select * from latest
