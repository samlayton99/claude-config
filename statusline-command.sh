#!/bin/sh
input=$(cat)

# Model name
model=$(echo "$input" | grep -o '"display_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"display_name"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')

# Output style
style=$(echo "$input" | grep -o '"output_style"[[:space:]]*:[[:space:]]*{[^}]*}' | grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')

# Context window usage (first used_percentage match)
ctx_raw=$(echo "$input" | grep -o '"used_percentage"[[:space:]]*:[[:space:]]*[0-9][0-9.]*' | head -1 | awk -F: '{print $2}' | tr -d ' ')

# Weekly rate limit: extract the seven_day block, then its used_percentage
seven_day_block=$(echo "$input" | grep -o '"seven_day"[[:space:]]*:[[:space:]]*{[^}]*}')
week_raw=$(echo "$seven_day_block" | grep -o '"used_percentage"[[:space:]]*:[[:space:]]*[0-9][0-9.]*' | awk -F: '{print $2}' | tr -d ' ')

# 5-hour session rate limit
five_hour_block=$(echo "$input" | grep -o '"five_hour"[[:space:]]*:[[:space:]]*{[^}]*}')
session_raw=$(echo "$five_hour_block" | grep -o '"used_percentage"[[:space:]]*:[[:space:]]*[0-9][0-9.]*' | awk -F: '{print $2}' | tr -d ' ')

[ -z "$model" ] && model="unknown"

parts="$model"
[ -n "$style" ] && [ "$style" != "default" ] && parts="$parts | $style"
[ -n "$ctx_raw" ] && parts="$parts | ctx: $(printf '%.0f' "$ctx_raw")%"
[ -n "$session_raw" ] && parts="$parts | session: $(printf '%.0f' "$session_raw")%"
[ -n "$week_raw" ] && parts="$parts | week: $(printf '%.0f' "$week_raw")%"

echo "$parts"
