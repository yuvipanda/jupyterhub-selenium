# Use dummy authenticator, accepts all usernames and all passwords as legit
c.JupyterHub.authenticator_class = 'dummyauthenticator.DummyAuthenticator'

# SimpleLocalProcessSpawner doesn't need user accounts to be setup in the
# local machine to spawn notebooks for them
c.JupyterHub.spawner_class = 'simplespawner.SimpleLocalProcessSpawner'
