RESOURCE_GROUP ?= rg2
TEMPLATE_FILE = deployment/main.bicep
PARAMETERS_FILE = parameters.json
DEPLOYMENT_NAME = psr_dep1
FUNCTION_APP_NAME = psrfunc

.PHONY: all
all: deploy

.PHONY: deploy
deploy: deploy-function

.PHONY: deploy-bicep
deploy-bicep:
	@echo "--- Deploying Bicep templates ---"
	az deployment group create \
		--resource-group $(RESOURCE_GROUP) \
		--template-file $(TEMPLATE_FILE) \
		--parameters @$(PARAMETERS_FILE) \
		--name $(DEPLOYMENT_NAME) \
		--mode Incremental # Or Complete, but be careful with Complete!
	@echo "--- Bicep deployment complete ---"

.PHONY: validate-bicep
validate-bicep:
	@echo "--- Validating Bicep templates ---"
	az deployment group validate \
		--resource-group $(RESOURCE_GROUP) \
		--template-file $(TEMPLATE_FILE) \
		--parameters @$(PARAMETERS_FILE)
	@echo "--- Bicep validation complete ---"

.PHONY: deploy-function
deploy-function: 
	@echo "--- Deploying Azure Function ---"
	cd psrfunc_app/; func azure functionapp publish psrfunc; cd ..;
	@echo "--- Function deployment complete ---"