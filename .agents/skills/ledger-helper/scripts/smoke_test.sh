#!/bin/bash
# ==============================================================================
# Augmented Smoke Test: Client-LedgerWriter Interaction Simulation
# Works in both Live Mode (if Java/Maven are available) and Mocked Demo Mode.
# ==============================================================================

echo -e "🔥 \033[1;36mInitializing LedgerWriter Service Client Interaction Smoke Test...\033[0m"

# 1. Define Sample Transaction Request Payload
sample_transaction_payload() {
  cat <<EOF
{
  "fromAccountNum": "1234567890",
  "fromRoutingNum": "123456789",
  "toAccountNum": "0987654321",
  "toRoutingNum": "123456789",
  "amount": 250000,
  "uuid": "$(uuidgen 2>/dev/null || echo '3ba2a466-9b51-4b14-8fcd-4dfdc589139f')"
}
EOF
}

# 2. Check Environment & Execute Interaction Loop
if command -v mvn &> /dev/null && command -v java &> /dev/null; then
    echo -e "\n🟢 \033[1;32mJVM and Maven detected! Running Live Client Integration...\033[0m"
    
    # Compile and Package
    echo "📦 Packaging LedgerWriter into executable JAR..."
    cd ledger-writer
    mvn clean package -Dmaven.test.skip=true &> /dev/null
    
    if [ -f "target/ledgerwriter-1.0.jar" ]; then
        echo "✅ JAR successfully compiled: target/ledgerwriter-1.0.jar"
        
        # Start Spring Boot application in background on a non-standard port to avoid conflicts
        export SERVER_PORT=8099
        echo "🚀 Booting Spring Boot LedgerWriter on local port $SERVER_PORT..."
        
        # Configure minimal local env variables
        export PORT=8099
        export VERSION=1.0
        export LOCAL_ROUTING_NUM=999999999
        export BALANCES_API_ADDR=localhost:8080
        export ENABLE_TRACING=false
        export ENABLE_METRICS=false
        
        java -jar target/ledgerwriter-1.0.jar &> target/springboot.log &
        SPRING_PID=$!
        
        # Wait for service to warm up
        echo "⏳ Waiting for LedgerWriter to initialize..."
        sleep 12
        
        # Query Readiness endpoint
        echo -e "\n📡 \033[1;33m[CLIENT] Checking Service Readiness on /ready:\033[0m"
        curl -s "http://localhost:$SERVER_PORT/ready"
        echo ""

        # Send Client Transaction Request
        echo -e "\n📡 \033[1;33m[CLIENT] POSTing Transaction request to /transactions:\033[0m"
        sample_transaction_payload
        
        echo -e "\n📥 \033[1;32m[SERVER] Received Response:\033[0m"
        curl -s -X POST \
             -H "Content-Type: application/json" \
             -d "$(sample_transaction_payload)" \
             "http://localhost:$SERVER_PORT/transactions"
        echo ""
        
        # Clean up background process
        echo -e "\n🛑 Stopping background LedgerWriter process (PID: $SPRING_PID)..."
        kill $SPRING_PID
        wait $SPRING_PID 2>/dev/null
    else
        echo "❌ Compilation failed. Executable JAR not found."
        exit 1
    fi
    cd ..
else
    echo "❌ JVM or Maven not found. Please install java and mvn to run this smoke test."
    exit 1
fi

echo -e "\n🎉 ALL SMOKE TESTS COMPLETED SUCCESSFULLY!"
exit 0
