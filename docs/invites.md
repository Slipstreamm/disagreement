# Working with Invites

The library exposes helper methods for creating and deleting invites.

## Create an Invite

```python
invite = await client.create_invite("1234567890", {"max_age": 3600})
print(invite.code)
```

## Delete an Invite

```python
await client.delete_invite(invite.code)
```

## List Invites

```python
invites = await client.fetch_invites("1234567890")
for inv in invites:
    print(inv.code, inv.uses)
```
