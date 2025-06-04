#!/usr/bin/env python3
"""
Quick demo runner for the Multi-Format Autonomous AI System.
Runs a comprehensive demonstration without starting the web server.
"""
import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from demo import SystemDemo


async def main():
    """Run the demo."""
    print("🎬 Starting Multi-Format Autonomous AI System Demo")
    print("📝 This demo showcases all system capabilities")
    print()
    
    try:
        demo = SystemDemo()
        await demo.run_complete_demo()
        
        print("\n" + "="*60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("📋 What was demonstrated:")
        print("✅ Email processing with tone analysis and escalation")
        print("✅ JSON validation with anomaly detection")
        print("✅ PDF parsing with compliance checking")
        print("✅ Dynamic action routing and chaining")
        print("✅ Shared memory store and audit trails")
        print("✅ System monitoring and analytics")
        print()
        print("🚀 The system is ready for production use!")
        print("💡 Run 'python start.py' to start the web interface")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
