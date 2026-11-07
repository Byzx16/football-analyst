create table if not exists competitions (
    id serial primary key,
    slug text unique not null,
    name text not null,
    type text not null
);

create table if not exists teams (
    id serial primary key,
    api_id int unique not null,
    name text not null,
    logo_url text
);

create table if not exists matches (
    id serial primary key,
    api_id int unique not null,
    competition_slug text references competitions(slug),
    home_team_id int references teams(id),
    away_team_id int references teams(id),
    kickoff_at timestamptz not null,
    status text default 'NS',
    home_score int,
    away_score int
);
create index on matches (kickoff_at, competition_slug);

create table if not exists team_form (
    team_id int references teams(id),
    competition_slug text,
    last5 text,                -- "WWDLW"
    goals_for int, goals_against int,
    xg_for numeric, xg_against numeric,
    updated_at timestamptz default now(),
    primary key (team_id, competition_slug)
);

create table if not exists injuries (
    id serial primary key,
    team_id int references teams(id),
    player_name text,
    position text,
    status text,          -- "out", "doubtful"
    reason text,
    updated_at timestamptz default now()
);

create table if not exists news (
    id serial primary key,
    team_id int references teams(id),
    title text, summary text, url text,
    source text, sentiment text,   -- positive/negative/neutral
    published_at timestamptz
);

create table if not exists odds_snapshot (
    id serial primary key,
    match_id int references matches(id),
    market text,           -- "h2h", "totals_2.5", "ah_-0.5"
    selection text,        -- "home", "draw", "away", "over", "under", "1", "2"
    odds_value numeric,
    bookmaker text,
    captured_at timestamptz default now()
);

create table if not exists analyses (
    id serial primary key,
    match_id int references matches(id),
    generated_at timestamptz default now(),
    model text,
    -- Hasil prediksi
    home_win_prob numeric,
    draw_prob numeric,
    away_win_prob numeric,
    predicted_score text,
    over_25_prob numeric,
    under_25_prob numeric,
    over_35_prob numeric,
    under_35_prob numeric,
    handicap_line numeric,     -- -0.5, +0.5, dst (dari sisi home)
    handicap_side text,        -- "home", "away"
    -- Value bets
    value_bets jsonb,          -- [{market, selection, model_prob, implied_prob, odds, edge}]
    key_factors jsonb,
    risks jsonb,
    news_summary text,
    injury_impact text,
    confidence text            -- low / medium / high
);

create table if not exists parlays (
    id serial primary key,
    generated_at timestamptz default now(),
    kind text,                 -- "winner", "over_under", "handicap", "mixed"
    legs jsonb,                -- [{match_id, market, selection, odds, model_prob, edge}]
    combined_odds numeric,
    combined_edge numeric,
    notes text
);