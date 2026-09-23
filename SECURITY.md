# Security policy

## Reporting a vulnerability

Report privately through **GitHub → Security → Report a vulnerability** on
this repository, or write to contact@nyquist.pro with "security" in the
subject. Please do not open a public issue.

We answer within three working days. Nyquist is run by its three founders,
there is no dedicated security team, and no bug bounty.

## Scope

The code in this repository: the `nyquist-sdk` client and `nyq` CLI, and the
`nyquist-mcp` server. Issues in the Nyquist platform itself (api.nyquist.pro,
the portal) are welcome through the same channel.

## Handling of your API key

- The key is sent only in the `X-API-Key` header, only over HTTPS — plain
  `http://` is refused for any host outside loopback and private networks.
- `nyq login` stores it in `~/.nyquist/config.json`, readable by you only
  (0600), written atomically.
- Error messages never quote the key.
