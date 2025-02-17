# mondossierweb

Get grades and detect changes in your grades, on schools using mon dossier web (mdw.(school domain))

## Installation

```bash
pip install mondossierweb
```

## Usage

### Classique

```
Usage: mondossierweb [SAVE_AS] [URL] [GRADE_CODE] [USERNAME] [PASSWORD_COMMAND]
       mondossierweb --help

Environment variables:
    MDW_USE_CACHE: if set, the HTML will be cached to mdw.html and will be reused if it exists.
```

### Docker

First copy .env.exemple
```sh
cp .env.example .env
```

Then you can edit `.env`

```
SAVE_AS=grades.json
URL=https://mdw.inp-toulouse.fr
GRADE_CODE=N7I51
USERNAME= <Your username>
PASSWORD_COMMAND=echo '<Your password>'
MDW_USE_CACHE=1
GOTIFY_URL="<Your gotify instance url>"
GOTIFY_APP_TOKEN="<The gotify app token created for the parser>"
CRON_SCHEDULE="*/5 * * * *"
HIDE_GRADES=1
NTFY_URL=https://ntfy.sh/mytopic
```

## Hiding grades

If you want to hide grades, you can set the `HIDE_GRADES` environment variable to `1`. This will hide the grades in the notification.

## Running with cron

Running with cron is easy, just run the following command:

```sh
    docker-compose --profile=cron up -d
```

The CRON_SCHEDULE is a cron schedule, you can use [crontab.guru](https://crontab.guru/) to help you.

## Known `GRADE_CODE`s

| School   | Year | Department | `GRADE_CODE` |
| -------- | ---- | ---------- | ------------ |
| ENSEEIHT | 1A   | 3EA        | `N7I41`      |
| ENSEEIHT | 2A   | 3EA        | `N7I42`      |
| ENSEEIHT | 3A   | 3EA        | `N7I43`      |
| ENSEEIHT | 1A   | SN         | `N7I51`      |
| ENSEEIHT | 2A   | SN         | `N7I52`      |
| ENSEEIHT | 3A   | SN         | `N7I53`      |
| ENSEEIHT | 3A   | PSMSC      | `N7X062`     |

