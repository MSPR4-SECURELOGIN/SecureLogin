# Windows PowerShell start script
$ErrorActionPreference = 'Stop'

function Check-Command($cmd) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "$cmd is required but not installed."
        exit 1
    }
}

foreach ($cmd in 'docker','kubectl','helm','faas-cli') { Check-Command $cmd }

$namespace = kubectl get namespace openfaas --no-headers 2>$null
if (-not $namespace) {
    Write-Host 'Installing OpenFaaS via helm...'
    helm repo add openfaas https://openfaas.github.io/faas-netes/
    kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml
    $PASSWORD = -join ((65..90) + (97..122) | Get-Random -Count 12 | % {[char]$_})
    kubectl -n openfaas create secret generic basic-auth \
        --from-literal=basic-auth-user=admin \
        --from-literal=basic-auth-password=$PASSWORD
    helm upgrade --install openfaas openfaas/openfaas \
        --namespace openfaas \
        --set basic_auth=true \
        --set functionNamespace=openfaas-fn \
        --set serviceType=NodePort \
        --wait
} else {
        $enc = kubectl -n openfaas get secret basic-auth -o jsonpath='{.data.basic-auth-password}';
    $PASSWORD = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($enc))
    Write-Host 'OpenFaaS already installed.'
}

$pf = Start-Process kubectl -ArgumentList '-n openfaas port-forward svc/gateway 8080:8080' -PassThru
Start-Sleep -Seconds 5

kubectl apply -f postgres-init.yaml
kubectl apply -f postgres-deployment.yaml

kubectl -n openfaas wait --for=condition=ready pod -l app=postgres --timeout=180s

Get-ChildItem -Path functions -Recurse -Filter stack.yml | ForEach-Object {
    faas-cli deploy -f $_.FullName
}

(Get-Content frontend/script.js) -replace 'const faasPassword = ".*";', "const faasPassword = \"$PASSWORD\";" | Set-Content frontend/script.js

docker compose up -d

Write-Host "`nFrontend available at http://localhost:8081"
Write-Host "OpenFaaS gateway at http://localhost:8080 (admin/$PASSWORD)"
Write-Host 'Press Ctrl+C to stop port-forwarding when finished.'
Wait-Process $pf.Id
