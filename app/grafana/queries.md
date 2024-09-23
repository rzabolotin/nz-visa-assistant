# Grafana Dashboard SQL Queries

## 1. Total Dialogs Over Time

```sql
SELECT
    date_trunc('day', timestamp) as date,
    COUNT(*) as total_dialogs
FROM
    dialogs
GROUP BY
    date_trunc('day', timestamp)
ORDER BY
    date
```

This query will show the total number of dialogs per day, allowing you to track conversation volume over time.

## 2. Average Token Counts

```sql
SELECT
    date_trunc('day', timestamp) as date,
    AVG(main_prompt_token_count) as avg_prompt_tokens,
    AVG(system_tokens_count) as avg_system_tokens,
    AVG(output_tokens_count) as avg_output_tokens
FROM
    dialogs
GROUP BY
    date_trunc('day', timestamp)
ORDER BY
    date
```

This query calculates the daily average token counts for main prompts, system messages, and outputs.

## 3. Language Distribution

```sql
SELECT
    COALESCE(language, "N/A") as language,
    COUNT(*) as dialog_count
FROM
    dialogs
GROUP BY
    language
ORDER BY
    dialog_count DESC
```

This query shows the distribution of dialogs across different languages.

## 4. User Activity

```sql
SELECT
    user_id,
    COUNT(*) as dialog_count
FROM
    dialogs
GROUP BY
    user_id
ORDER BY
    dialog_count DESC
LIMIT 10
```

This query lists the top 10 most active users based on their dialog count.

## 5. Feedback history

```sql
SELECT
    date_trunc('day', f.timestamp) as date,
    SUM(case when f.is_positive then 1 else 0 end) as positive,
    SUM(case when f.is_positive then 0 else 1 end) as negative
FROM
    dialogs d
JOIN
    feedback f ON d.id = f.dialog_id
GROUP BY
    date_trunc('day', f.timestamp)

```

The timeseries of user's feedback


## 6. Token Usage Trends

```sql
SELECT
    date_trunc('day', timestamp) as day,
    SUM(main_prompt_token_count) as total_prompt_tokens,
    SUM(system_tokens_count) as total_system_tokens,
    SUM(output_tokens_count) as total_output_tokens
FROM
    dialogs
GROUP BY
    date_trunc('day', timestamp)
ORDER BY
    day
```

This query shows weekly trends in token usage across different types (prompt, system, output).

## 7. Most recent dialogs

```sql
SELECT
    user_id,
    query,
    answer
FROM
    dialogs
ORDER BY
    timestamp DESC
LIMIT 10
```

This query displays the most recent dialogs, including the user ID, query, and answer.
