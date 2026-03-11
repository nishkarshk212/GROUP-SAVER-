#!/bin/bash
# SSH Key Setup Helper for Deployment
# This helps you setup SSH keys for passwordless deployment

echo "=============================================="
echo "SSH Key Setup for Bot Deployment"
echo "=============================================="
echo ""

# Check for existing SSH keys
echo "🔑 Checking for existing SSH keys..."
echo ""

if [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ Found existing RSA key: ~/.ssh/id_rsa.pub"
    SHOW_KEY="y"
elif [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✅ Found existing ED25519 key: ~/.ssh/id_ed25519.pub"
    SHOW_KEY="y"
else
    echo "❌ No SSH key found"
    echo ""
    echo "Would you like to generate a new SSH key? (y/n)"
    read -r GENERATE_KEY
    
    if [[ $GENERATE_KEY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Generating new SSH key..."
        echo "Enter passphrase (press enter for no passphrase):"
        ssh-keygen -t ed25519 -C "your_email@example.com"
        
        if [ -f ~/.ssh/id_ed25519.pub ]; then
            echo "✅ Key generated successfully!"
            SHOW_KEY="y"
        else
            echo "❌ Key generation failed"
            exit 1
        fi
    else
        echo "Exiting without generating key"
        exit 0
    fi
fi

# Display public key
if [[ $SHOW_KEY == "y" ]]; then
    echo ""
    echo "=============================================="
    echo "Your SSH Public Key:"
    echo "=============================================="
    echo ""
    
    if [ -f ~/.ssh/id_rsa.pub ]; then
        cat ~/.ssh/id_rsa.pub
        PUB_KEY_FILE=~/.ssh/id_rsa.pub
    elif [ -f ~/.ssh/id_ed25519.pub ]; then
        cat ~/.ssh/id_ed25519.pub
        PUB_KEY_FILE=~/.ssh/id_ed25519.pub
    fi
    
    echo ""
    echo "=============================================="
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. Copy the public key above (entire line)"
    echo ""
    echo "2. SSH into your server manually:"
    echo "   ssh root@140.245.240.202 -p 22"
    echo ""
    echo "3. On the server, run:"
    echo "   mkdir -p ~/.ssh"
    echo "   nano ~/.ssh/authorized_keys"
    echo ""
    echo "4. Paste your public key and save (Ctrl+X, Y, Enter)"
    echo ""
    echo "5. Set correct permissions:"
    echo "   chmod 700 ~/.ssh"
    echo "   chmod 600 ~/.ssh/authorized_keys"
    echo ""
    echo "6. Test connection:"
    echo "   ssh root@140.245.240.202 -p 22"
    echo ""
    echo "=============================================="
    echo ""
    
    # Option to copy key to server automatically
    echo "Would you like to try copying the key automatically? (requires password once)"
    echo "y/n"
    read -r AUTO_COPY
    
    if [[ $AUTO_COPY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Copying SSH key to server..."
        echo "You'll be prompted for the server password once."
        echo ""
        
        if command -v ssh-copy-id &> /dev/null; then
            ssh-copy-id -p 22 root@140.245.240.202
            echo ""
            echo "✅ Key copied successfully!"
            echo ""
            echo "Testing connection..."
            if ssh -p 22 -o BatchMode=yes root@140.245.240.202 exit 2>/dev/null; then
                echo "✅ Passwordless SSH working!"
                echo ""
                echo "🎉 You can now run: ./deploy_auto.sh"
            else
                echo "⚠️  Connection test failed. Please check the setup manually."
            fi
        else
            echo "❌ ssh-copy-id not found on your system."
            echo "Please follow the manual steps above."
        fi
    fi
fi

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Once SSH key is configured, you can deploy with:"
echo "  ./deploy_auto.sh"
echo ""
