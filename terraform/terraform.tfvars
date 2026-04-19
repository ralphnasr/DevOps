aws_region = "us-east-1"

admin_cidr_blocks  = ["82.146.174.168/32"]
bastion_key_name   = "shopcloud-bastion"
bastion_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAnwJngqkU7mKDnZToX5O5eWv8llr6f6hqb0eYyQoDz1 sarmad.farhat2017@gmail.com"

ses_verified_email = "sarmad.farhat2017@gmail.com"

domain_name = ""

# Phase-1 apply: localhost only. deploy.sh overrides with real CloudFront URL on phase 2.
customer_callback_urls = ["http://localhost:3000/callback.html"]
customer_logout_urls   = ["http://localhost:3000/index.html"]
admin_callback_urls    = ["http://localhost:8001/admin"]
admin_logout_urls      = ["http://localhost:8001/admin"]
