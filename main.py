import time
from agent import Agent
from environment import Environment
from random_agent import RandomAgent
from moving_wumpus_environment import MovingWumpusEnvironment
from adaptive_agent import AdaptiveAgent

def get_user_configuration():
    while True:
        try:
            N = int(input("Enter map size N (recommended 4-10, default 8): ") or 8)
            K = int(input(f"Enter number of wumpuses K (recommended 1-{N//2}, default 2): ") or 2)
            p = float(input("Enter pit density (0.0-0.5, recommended 0.1-0.2, default 0.2): ") or 0.2)
            mode = input("Choose mode (1=Intelligent Agent, 2=Random Agent, 3=Compare Agents, 4=Moving Wumpus Mode, default 1): ") or "1"
            break
        except ValueError:
            print("Please enter a valid number.")
    
    return N, K, p, mode

def run_autonomous_mode(env, agent, agent_type="Intelligent"):
    """Run the autonomous agent simulation with hybrid planning and inference."""
    step_count = 0
    max_steps = 200  # Prevent infinite loops
    print(f"Starting {agent_type.lower()} agent!")

    while step_count < max_steps:
        step_count += 1
        print(f"\n-Step {step_count}")

        # Display the real environment
        print("Real Environment:")
        env.print_map()
        
        # Get percepts from environment
        percepts = env.env_get_percepts()
        
        # Update agent's knowledge base with new percepts
        agent.Agent_get_percepts(percepts)
        
        # Display agent's knowledge map
        print(f"\n{agent_type} Agent's Knowledge:")
        agent.print_agent_map(env.N, env.N, env.agent_x, env.agent_y)
        
        # Display current score
        current_score = agent.calculate_current_score()
        print(f"\n📊 Current Score: {current_score} | Gold: {'✅' if agent.has_gold else '❌'}")

        # Agent decides next action
        action = agent.choose_action()
        print(f"\n🎯 {agent_type} Agent chooses action: {action}")
        
        # Execute the action
        if action == "FORWARD":
            died, bump = env.move_forward()
            agent.move_forward_action()  # Apply movement cost -1
            if died:
                agent.die_action()  # Apply death penalty -1000
                print("💀 GAME OVER! Agent died!")
                break
            if bump:
                print("💥 BUMP! Hit a wall!")
        elif action == "LEFT":
            env.turn_left()
            agent.turn_action()  # Apply turn cost -1
            print("↺ Turned left")
        elif action == "RIGHT":
            env.turn_right()
            agent.turn_action()  # Apply turn cost -1
            print("↻ Turned right")
        elif action == "SHOOT":
            if agent.shoot_action():  # Apply shooting cost -10
                env.shoot()
                if env.scream:
                    print("🎯 SCREAM! Wumpus killed!")
                else:
                    print("🏹 Arrow shot, but no scream...")
        elif action == "GRAB":
            # Check if agent can grab gold (sees glitter)
            if agent.grab_gold_action():  # Apply gold bonus +10
                # Environment removes gold from the cell
                env.grab_gold()
            else:
                pass  # Error message already printed in agent method
        elif action == "CLIMB":
            if agent.climb_action():  # Apply climb bonus +1000 or +0
                if env.climb():
                    final_score = agent.calculate_current_score()
                    print("🎉 MISSION COMPLETE! Agent successfully escaped with the gold!")
                    print(f"🏆 FINAL SCORE: {final_score}")
                    break
            else:
                if env.agent_x == 0 and env.agent_y == 0:
                    print("❌ Cannot climb without gold!")
                else:
                    print("❌ Can only climb at starting position (0,0)!")
        elif action == "QUIT":
            print("Agent has no safe moves available. Exploration ended.")
            break
        
        # Small delay for readability
        time.sleep(0.5)

    final_score = agent.calculate_current_score()
    print(f"\n" + "="*60)
    print(f"📈 {agent_type.upper()} AGENT SIMULATION SUMMARY")
    print(f"="*60)
    print(f"Total Steps: {step_count}")
    print(f"Final Score: {final_score}")
    print(f"Agent Position: ({env.agent_x}, {env.agent_y})")
    if hasattr(agent, 'kb'):
        print(f"Cells Visited: {len(agent.kb.visited)}/{env.N * env.N}")
    else:
        print(f"Cells Visited: {len(agent.visited)}/{env.N * env.N}")
    print(f"Gold Retrieved: {'✅ Yes' if agent.has_gold else '❌ No'}")
    print(f"Mission Status: {'🎉 SUCCESS' if agent.has_gold and env.agent_x == 0 and env.agent_y == 0 else '❌ INCOMPLETE'}")
    print(f"\n📊 SCORING BREAKDOWN:")
    print(f"   • Grab Gold: +10 {'✅' if agent.has_gold else '❌'}")
    print(f"   • Move Forward: -1 per move")
    print(f"   • Turn Left/Right: -1 per turn")
    print(f"   • Shoot Arrow: -10 {'✅' if agent.shoot else '❌'}")
    print(f"   • Climb Out (with gold): +1000 {'✅' if agent.has_gold and env.agent_x == 0 and env.agent_y == 0 else '❌'}")
    print(f"   • Die: -1000 {'❌' if final_score <= -1000 else '✅'}")
    
    return final_score, step_count, agent.has_gold, (env.agent_x == 0 and env.agent_y == 0)

def run_comparison_experiment(N, K, p, num_trials=10):
    """
    Run comparison experiments between intelligent agent and random agent.
    """
    print(f"\n{'='*80}")
    print(f"🧪 AGENT COMPARISON EXPERIMENT")
    print(f"{'='*80}")
    print(f"Configuration: {N}x{N} map, {K} wumpuses, {p} pit density")
    print(f"Running {num_trials} trials for each agent...")
    
    intelligent_results = []
    random_results = []
    
    for trial in range(num_trials):
        print(f"\n🔬 Trial {trial + 1}/{num_trials}")
        print("-" * 40)
        
        # Test intelligent agent
        print(f"Testing Intelligent Agent...")
        env_intelligent = Environment(N=N, K=K, p=p)
        agent_intelligent = Agent(N)
        score_i, steps_i, has_gold_i, climbed_i = run_autonomous_mode(env_intelligent, agent_intelligent, "Intelligent")
        intelligent_results.append({
            'score': score_i,
            'steps': steps_i,
            'has_gold': has_gold_i,
            'success': has_gold_i and climbed_i,
            'survived': score_i > -1000
        })
        
        print(f"\n" + "-" * 40)
        
        # Test random agent on same configuration
        print(f"Testing Random Agent...")
        env_random = Environment(N=N, K=K, p=p)
        agent_random = RandomAgent(N)
        score_r, steps_r, has_gold_r, climbed_r = run_autonomous_mode(env_random, agent_random, "Random")
        random_results.append({
            'score': score_r,
            'steps': steps_r,
            'has_gold': has_gold_r,
            'success': has_gold_r and climbed_r,
            'survived': score_r > -1000
        })
    
    # Calculate statistics
    print(f"\n{'='*80}")
    print(f"📊 EXPERIMENT RESULTS SUMMARY")
    print(f"{'='*80}")
    
    # Intelligent Agent Stats
    i_scores = [r['score'] for r in intelligent_results]
    i_steps = [r['steps'] for r in intelligent_results]
    i_success_rate = sum(r['success'] for r in intelligent_results) / num_trials * 100
    i_survival_rate = sum(r['survived'] for r in intelligent_results) / num_trials * 100
    i_gold_rate = sum(r['has_gold'] for r in intelligent_results) / num_trials * 100
    
    print(f"\n🤖 INTELLIGENT AGENT PERFORMANCE:")
    print(f"   • Average Score: {sum(i_scores)/len(i_scores):.1f}")
    print(f"   • Best Score: {max(i_scores)}")
    print(f"   • Worst Score: {min(i_scores)}")
    print(f"   • Average Steps: {sum(i_steps)/len(i_steps):.1f}")
    print(f"   • Success Rate: {i_success_rate:.1f}% (found gold + escaped)")
    print(f"   • Survival Rate: {i_survival_rate:.1f}% (didn't die)")
    print(f"   • Gold Finding Rate: {i_gold_rate:.1f}%")
    
    # Random Agent Stats
    r_scores = [r['score'] for r in random_results]
    r_steps = [r['steps'] for r in random_results]
    r_success_rate = sum(r['success'] for r in random_results) / num_trials * 100
    r_survival_rate = sum(r['survived'] for r in random_results) / num_trials * 100
    r_gold_rate = sum(r['has_gold'] for r in random_results) / num_trials * 100
    
    print(f"\n🎲 RANDOM AGENT PERFORMANCE:")
    print(f"   • Average Score: {sum(r_scores)/len(r_scores):.1f}")
    print(f"   • Best Score: {max(r_scores)}")
    print(f"   • Worst Score: {min(r_scores)}")
    print(f"   • Average Steps: {sum(r_steps)/len(r_steps):.1f}")
    print(f"   • Success Rate: {r_success_rate:.1f}% (found gold + escaped)")
    print(f"   • Survival Rate: {r_survival_rate:.1f}% (didn't die)")
    print(f"   • Gold Finding Rate: {r_gold_rate:.1f}%")
    
    # Comparison
    print(f"\n📈 PERFORMANCE COMPARISON:")
    score_improvement = (sum(i_scores)/len(i_scores)) - (sum(r_scores)/len(r_scores))
    print(f"   • Score Improvement: {score_improvement:+.1f} points")
    print(f"   • Success Rate Improvement: {i_success_rate - r_success_rate:+.1f}%")
    print(f"   • Survival Rate Improvement: {i_survival_rate - r_survival_rate:+.1f}%")
    print(f"   • Efficiency: Intelligent agent is {(sum(r_steps)/len(r_steps))/(sum(i_steps)/len(i_steps)):.1f}x more efficient")
    
    return intelligent_results, random_results

def run_moving_wumpus_mode(env, agent, agent_type="Intelligent"):
    """Run simulation with moving wumpuses that move every 5 actions."""
    step_count = 0
    max_steps = 300  # Increase max steps for dynamic environment
    print(f"🐺 Starting {agent_type.lower()} agent in Moving Wumpus mode!")
    print("⚠️  WARNING: Wumpuses move every 5 actions - previous knowledge may become outdated!")

    while step_count < max_steps:
        step_count += 1
        print(f"\n--- Step {step_count} ---")

        # Display the real environment
        print("Real Environment:")
        env.print_map()
        
        # Get percepts from environment
        percepts = env.env_get_percepts()
        
        # Update agent's knowledge base with new percepts
        agent.Agent_get_percepts(percepts)
        
        # Handle wumpus movement detection for adaptive agents
        if hasattr(agent, 'handle_wumpus_movement_phase'):
            wumpus_moved = agent.handle_wumpus_movement_phase(env.action_count)
            if wumpus_moved:
                print("🧠 Adaptive agent detected and handled wumpus movement phase")
        
        # Display agent's knowledge map
        print(f"\n{agent_type} Agent's Knowledge:")
        agent.print_agent_map(env.N, env.N, env.agent_x, env.agent_y)
        
        # Display current score and action count
        current_score = agent.calculate_current_score()
        actions_until_wumpus_move = 5 - (env.action_count % 5)
        print(f"\n📊 Score: {current_score} | Gold: {'✅' if agent.has_gold else '❌'} | Actions until Wumpus move: {actions_until_wumpus_move}")

        # Agent decides next action
        action = agent.choose_action()
        print(f"\n🎯 {agent_type} Agent chooses action: {action}")
        
        # Execute the action with dynamic environment handling
        agent_died = False
        
        if action == "FORWARD":
            died, bump = env.move_forward()
            agent.move_forward_action()
            if died:
                agent.die_action()
                agent_died = True
                if env.check_wumpus_collision():
                    print("💀 GAME OVER! Agent was eaten by a moving Wumpus!")
                else:
                    print("💀 GAME OVER! Agent died!")
                break
            if bump:
                print("💥 BUMP! Hit a wall!")
                
        elif action == "LEFT":
            died = env.turn_left()
            agent.turn_action()
            if died:
                agent.die_action()
                print("💀 GAME OVER! Agent was eaten by a moving Wumpus!")
                break
            print("↺ Turned left")
            
        elif action == "RIGHT":
            died = env.turn_right()
            agent.turn_action()
            if died:
                agent.die_action()
                print("💀 GAME OVER! Agent was eaten by a moving Wumpus!")
                break
            print("↻ Turned right")
            
        elif action == "SHOOT":
            if agent.shoot_action():
                died = env.shoot()
                if died:
                    agent.die_action()
                    print("💀 GAME OVER! Agent was eaten by a moving Wumpus!")
                    break
                if env.scream:
                    print("🎯 SCREAM! Wumpus killed!")
                    # Agent should update knowledge about killed wumpus
                    if hasattr(agent, 'inference_engine'):
                        agent.inference_engine.handle_shoot(env.agent_x, env.agent_y, env.agent_dir)
                else:
                    print("🏹 Arrow shot, but no scream...")
                    
        elif action == "GRAB":
            if agent.grab_gold_action():
                env.grab_gold()
                # Check if wumpus moved during grab action
                if env.check_wumpus_collision():
                    agent.die_action()
                    print("💀 GAME OVER! Agent was eaten by a moving Wumpus during grab!")
                    break
                    
        elif action == "CLIMB":
            if agent.climb_action():
                if env.climb():
                    final_score = agent.calculate_current_score()
                    print("🎉 MISSION COMPLETE! Agent successfully escaped with the gold!")
                    print(f"🏆 FINAL SCORE: {final_score}")
                    break
            else:
                if env.agent_x == 0 and env.agent_y == 0:
                    print("❌ Cannot climb without gold!")
                else:
                    print("❌ Can only climb at starting position (0,0)!")
                    
        elif action == "QUIT":
            print("Agent has no safe moves available. Exploration ended.")
            break
        
        # After wumpus movement, run inference again to update knowledge
        if env.action_count % 5 == 0 and hasattr(agent, 'inference_engine'):
            print("🧠 Re-running inference after Wumpus movement...")
            agent.inference_engine.logic_inference_forward_chaining()
        
        # Small delay for readability
        time.sleep(0.7)

    final_score = agent.calculate_current_score()
    print(f"\n" + "="*70)
    print(f"📈 {agent_type.upper()} AGENT - MOVING WUMPUS SIMULATION SUMMARY")
    print(f"="*70)
    print(f"Total Steps: {step_count}")
    print(f"Total Actions: {env.action_count}")
    print(f"Wumpus Movements: {env.action_count // 5}")
    print(f"Final Score: {final_score}")
    print(f"Agent Position: ({env.agent_x}, {env.agent_y})")
    if hasattr(agent, 'kb'):
        print(f"Cells Visited: {len(agent.kb.visited)}/{env.N * env.N}")
    else:
        print(f"Cells Visited: {len(agent.visited)}/{env.N * env.N}")
    print(f"Gold Retrieved: {'✅ Yes' if agent.has_gold else '❌ No'}")
    print(f"Mission Status: {'🎉 SUCCESS' if agent.has_gold and env.agent_x == 0 and env.agent_y == 0 else '❌ INCOMPLETE'}")
    print(f"Final Wumpus Locations: {env.wumpus_locations}")
    
    print(f"\n📊 SCORING BREAKDOWN:")
    print(f"   • Grab Gold: +10 {'✅' if agent.has_gold else '❌'}")
    print(f"   • Move Forward: -1 per move")
    print(f"   • Turn Left/Right: -1 per turn")
    print(f"   • Shoot Arrow: -10 {'✅' if agent.shoot else '❌'}")
    print(f"   • Climb Out (with gold): +1000 {'✅' if agent.has_gold and env.agent_x == 0 and env.agent_y == 0 else '❌'}")
    print(f"   • Die: -1000 {'❌' if final_score <= -1000 else '✅'}")
    
    print(f"\n🐺 MOVING WUMPUS CHALLENGE ANALYSIS:")
    wumpus_movements = env.action_count // 5
    if wumpus_movements > 0:
        print(f"   • Wumpus moved {wumpus_movements} times during the game")
        print(f"   • Agent adapted to dynamic environment: {'✅ Yes' if final_score > -500 else '❌ Struggled'}")
        print(f"   • Risk Management: {'Excellent' if not agent_died else 'Failed - killed by moving Wumpus'}")
    else:
        print(f"   • No Wumpus movements occurred (game ended before 5 actions)")
    
    return final_score, step_count, agent.has_gold, (env.agent_x == 0 and env.agent_y == 0)

if __name__ == "__main__":
    N, K, p, mode = get_user_configuration()

    print(f"Map Size: {N}x{N}")
    print(f"Wumpuses: {K}")
    print(f"Pit Density: {p}")

    if mode == '1':
        print(f"Mode: Intelligent Agent")
        env = Environment(N=N, K=K, p=p) 
        agent = Agent(N)
        final_score, steps, has_gold, climbed = run_autonomous_mode(env, agent, "Intelligent")
        print(f"\n🎯 Intelligent Agent Performance Analysis:")
        print(f"   • Efficiency: {len(agent.kb.visited)}/{env.N * env.N} cells explored")
        print(f"   • Risk Management: {'Excellent' if final_score > 500 else 'Good' if final_score > 0 else 'Needs Improvement'}")
        print(f"   • Planning Effectiveness: {'Optimal' if agent.has_gold else 'Suboptimal'}")
    elif mode == '2':
        print(f"Mode: Random Agent Baseline")
        env = Environment(N=N, K=K, p=p) 
        agent = RandomAgent(N)
        final_score, steps, has_gold, climbed = run_autonomous_mode(env, agent, "Random")
        print(f"\n🎲 Random Agent Performance Analysis:")
        print(f"   • Efficiency: {len(agent.visited)}/{env.N * env.N} cells explored")
        print(f"   • Risk Management: {'Poor - Random decisions' if final_score < 0 else 'Lucky!'}")
        print(f"   • Planning Effectiveness: {'None - Pure randomness'}")
    elif mode == '3':
        print(f"Mode: Agent Comparison Experiment")
        num_trials = int(input("Enter number of trials per agent (default 5): ") or 5)
        run_comparison_experiment(N, K, p, num_trials)
    elif mode == '4':
        print(f"Mode: Moving Wumpus Mode")
        agent_choice = input("Choose agent type (1=Adaptive Agent, 2=Standard Agent, 3=Random Agent, default Adaptive): ") or "1"
        
        if agent_choice == '1':
            env = MovingWumpusEnvironment(N=N, K=K, p=p)
            agent = AdaptiveAgent(N)
            final_score, steps, has_gold, climbed = run_moving_wumpus_mode(env, agent, "Adaptive")
            print(f"\n🧠 Adaptive Agent in Moving Wumpus Environment:")
            print(f"   • Adaptability: {'Excellent' if final_score > 0 else 'Good' if final_score > -500 else 'Needs Improvement'}")
            print(f"   • Dynamic Planning: {'Effective' if has_gold else 'Challenged by moving threats'}")
            print(f"   • Survival: {'Success' if final_score > -1000 else 'Failed - killed by Wumpus'}")
            print(f"   • Movement Adaptation: {agent.movement_phases} wumpus movement phases handled")
            print(f"   • Knowledge Management: {'Effective' if len(agent.outdated_wumpus_knowledge) < 5 else 'Struggled with uncertainty'}")
        elif agent_choice == '2':
            env = MovingWumpusEnvironment(N=N, K=K, p=p)
            agent = Agent(N)
            final_score, steps, has_gold, climbed = run_moving_wumpus_mode(env, agent, "Standard")
            print(f"\n🤖 Standard Agent in Moving Wumpus Environment:")
            print(f"   • Adaptability: {'Limited - no dynamic knowledge management'}")
            print(f"   • Dynamic Planning: {'Basic - may struggle with moving threats'}")
            print(f"   • Survival: {'Success' if final_score > -1000 else 'Failed - killed by Wumpus'}")
        elif agent_choice == '3':
            env = MovingWumpusEnvironment(N=N, K=K, p=p)
            agent = RandomAgent(N)
            final_score, steps, has_gold, climbed = run_moving_wumpus_mode(env, agent, "Random")
            print(f"\n🎲 Random Agent in Moving Wumpus Environment:")
            print(f"   • Survival Rate: {'Lucky' if final_score > -1000 else 'Expected failure against moving threats'}")
            print(f"   • Adaptation: {'None - Pure randomness vs dynamic environment'}")
        else:
            print("Invalid agent choice.")
    else:
        print("Invalid mode selected.")