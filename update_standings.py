import re
import requests
import datetime
import os
import pandas as pd

CSV_FILE = "league_current_standings.csv"
COLUMNS = ['Nr', 'Team', 'Played', 'W', 'D', 'L', 'Goals', 'Goal Difference', 'Points', 'Date', 'week', 'Time']


def extrahera_text(json_data):
    try:
        sub_pages = json_data.get("data", {}).get("subPages", [])
        if sub_pages:
            return sub_pages[0].get("altText", "")
    except Exception:
        pass
    return None


def text_till_dataframe(clean_text):
    rows = []
    for line in clean_text.splitlines():
        line = line.strip()
        match = re.match(
            r'^(\d{1,2})\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d]+-[\d]+)\s+(\d+)$',
            line
        )
        if match:
            goals_str = match.group(7)
            scored, conceded = map(int, goals_str.split('-'))
            rows.append({
                'Nr':              int(match.group(1)),
                'Team':            match.group(2).strip(),
                'Played':          int(match.group(3)),
                'W':               int(match.group(4)),
                'D':               int(match.group(5)),
                'L':               int(match.group(6)),
                'Goals':           goals_str,
                'Goal Difference': scored - conceded,
                'Points':          int(match.group(8)),
            })
    return pd.DataFrame(rows)


def hamta_allsvenskan_df():
    url = "https://www.svt.se/text-tv/api/343"
    try:
        response = requests.get(url, timeout=10)
        json_data = response.json()
        raw_content = extrahera_text(json_data)

        if raw_content:
            clean_text = re.sub(r'<[^>]*>', '', raw_content)
            df = text_till_dataframe(clean_text)

            now = datetime.datetime.now()
            df['Date'] = now.date()
            df['week'] = now.isocalendar().week
            df['Time'] = now.strftime('%H:%M:%S')

            return df[COLUMNS]
        else:
            print("Kunde inte hitta texten.")
            return None
    except Exception as e:
        print(f"Fel: {e}")
        return None


def append_to_csv(df_new):
    if os.path.exists(CSV_FILE):
        df_existing = pd.read_csv(CSV_FILE, dtype=str)

        current_week = str(df_new['week'].iloc[0])
        current_year = str(df_new['Date'].iloc[0])[:4]

        already_exists = (
            (df_existing['week'] == current_week) &
            (df_existing['Date'].str[:4] == current_year)
        ).any()

        if already_exists:
            print(f"Vecka {current_week} redan inlagd — hoppar över.")
            return

        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_csv(CSV_FILE, index=False)
    print(f"CSV uppdaterad: {CSV_FILE} ({len(df_new)} rader tillagda)")


if __name__ == "__main__":
    df = hamta_allsvenskan_df()

    if df is not None and not df.empty:
        print(df.to_string(index=False))
        append_to_csv(df)
    else:
        print("Tabellen kunde inte skapas.")