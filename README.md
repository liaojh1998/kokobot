# kokobot
An amazing, awesome, super cool Discord bot UT Austin SASE.

## TODO
### Taken
- None

### Easy (discord.py, Python)
- Koko: Sanitize string input to have a maximum length.

### Medium (discord.py, Python, implementation stuff)
- Koko: `$koko modify` instead of `$koko remove` first then `$koko add`.
- Improve the `$help` messages (that is, make `$help koko` the same as `$koko help`).
- Add emoji create, delete, list, and search.

### Hard (discord.py, Python, sqlite3, ask me for Amazon credentials stuff)
- Custom emoji used counter in database for all messages. Need to include date added, and probably store emoji based on emoji id if there is (check discord.py API)?
- On custom emoji add, remove, or update, do database update.
- Add kokobot command counters in database.
- Do random fun things on kokobot like speech-to-text synthesis for deaf users.

### Very Hard (discord.py, Python, sqlite3, Amazon S3 APIs, ask me for Amazon credentials stuff)
- Use S3 API to save uploaded pics and files for notes (maximum file size to be 10 Mb?), and store their links into database.

## TODO (Low-Priority)
### Easy (Python)
- Fix Python packaging so that kokobot is a legit project and module.
