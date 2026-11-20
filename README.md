# SMS webhook

The application receives Telnyx SMS webhook events and generates replies with
OpenAI. After installing the project and configuring `OPENAI_API_KEY`,
`TELNYX_API_KEY`, `TELNYX_SENDER_ID`, and `TELNYX_PHONE_NUMBER`, start it with:

```sh
my-project
```

The server listens locally on port 5001 by default. Set `PORT` to run another
instance on a different port, for example:

```sh
PORT=5002 my-project
```
