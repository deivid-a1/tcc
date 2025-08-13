#!/usr/bin/env python3
"""
Comparação Técnica: Qwen2.5-14B-Instruct vs Qwen3-14B
Para TCC: Assistente Estudantil Web Descentralizada

Executa testes comparativos para decidir o modelo mais adequado
"""

import torch
import psutil
import time
import gc
import json
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import Dict, List, Tuple, Optional
import subprocess
import sys

class ModelComparator:
    def __init__(self):
        self.models = {
            "qwen2.5": {
                "name": "Qwen/Qwen2.5-14B-Instruct",
                "display_name": "Qwen2.5-14B-Instruct",
                "version": "2.5",
                "release_date": "Sep 2024"
            },
            "qwen3": {
                "name": "Qwen/Qwen3-14B", 
                "display_name": "Qwen3-14B",
                "version": "3.0",
                "release_date": "Apr 2025"
            }
        }
        
        self.test_scenarios = [
            {
                "name": "Basic Academic Query",
                "system": "You are an intelligent academic assistant for a university.",
                "prompt": "What are the operating hours of the computer science building?",
                "expected_behavior": "Should ask for clarification or suggest checking with administration"
            },
            {
                "name": "Function Calling Scenario",
                "system": "You have access to the function: get_room_availability(building: str, room: str) -> dict. Use it when needed.",
                "prompt": "Check if room 201 in the engineering building is available right now.",
                "expected_behavior": "Should attempt to call the function with correct parameters"
            },
            {
                "name": "Chain-of-Thought Reasoning",
                "system": "You are a helpful assistant. Think step by step before answering.",
                "prompt": "A student needs to reserve a lab for 3 hours, starting in 2 hours. The lab closes at 6 PM and it's currently 1 PM. Is this possible?",
                "expected_behavior": "Should show clear reasoning process and calculate the timeline"
            },
            {
                "name": "Multi-step Academic Task",
                "system": "You are an academic advisor assistant.",
                "prompt": "A student wants to know what courses they need to take next semester. They've completed Calculus I and Programming Basics. They're in Computer Science major.",
                "expected_behavior": "Should identify need for prerequisite information and suggest logical next steps"
            },
            {
                "name": "Structured Output",
                "system": "Respond in JSON format when requested.",
                "prompt": "List 3 study tips in JSON format with fields: tip_number, title, description.",
                "expected_behavior": "Should produce valid JSON structure"
            }
        ]
        
        self.results = {}

    def check_system_resources(self) -> bool:
        """Verifica recursos disponíveis"""
        print("=== SYSTEM RESOURCE CHECK ===")
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"✅ GPU: {gpu_name}")
            print(f"✅ Total VRAM: {total_memory:.1f}GB")
        else:
            print("❌ CUDA not available!")
            return False
        
        ram_gb = psutil.virtual_memory().total / (1024**3)
        print(f"✅ Total RAM: {ram_gb:.1f}GB")
        return True

    def load_model(self, model_key: str) -> Optional[Dict]:
        """Carrega um modelo específico"""
        model_info = self.models[model_key]
        model_name = model_info["name"]
        
        print(f"\n--- Loading {model_info['display_name']} ---")
        
        # Quantization config
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        try:
            start_time = time.time()
            
            # Clear cache
            torch.cuda.empty_cache()
            gc.collect()
            
            print("Loading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            
            print("Loading model...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                quantization_config=quantization_config
            )
            
            load_time = time.time() - start_time
            memory_used = torch.cuda.memory_allocated(0) / (1024**3)
            
            print(f"✅ Model loaded successfully!")
            print(f"✅ Load time: {load_time:.1f}s")
            print(f"✅ VRAM used: {memory_used:.1f}GB")
            
            return {
                "model": model,
                "tokenizer": tokenizer,
                "load_time": load_time,
                "memory_used": memory_used,
                "model_info": model_info
            }
            
        except Exception as e:
            print(f"❌ Failed to load {model_info['display_name']}: {str(e)}")
            return None

    def run_inference_test(self, model_config: Dict, scenario: Dict) -> Dict:
        """Executa teste de inferência para um cenário"""
        model = model_config["model"]
        tokenizer = model_config["tokenizer"]
        
        print(f"\n  Testing: {scenario['name']}")
        
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": scenario["system"]},
                {"role": "user", "content": scenario["prompt"]}
            ]
            
            # Apply chat template
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Tokenize
            model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
            
            # Generate response
            start_time = time.time()
            
            with torch.no_grad():
                generated_ids = model.generate(
                    model_inputs.input_ids,
                    max_new_tokens=200,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=tokenizer.eos_token_id,
                    attention_mask=model_inputs.attention_mask if 'attention_mask' in model_inputs else None
                )
            
            generation_time = time.time() - start_time
            
            # Decode response
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Calculate tokens per second
            output_tokens = len(generated_ids[0])
            tokens_per_second = output_tokens / generation_time if generation_time > 0 else 0
            
            print(f"    ✅ Generated {output_tokens} tokens in {generation_time:.2f}s ({tokens_per_second:.1f} tok/s)")
            
            return {
                "success": True,
                "response": response,
                "generation_time": generation_time,
                "output_tokens": output_tokens,
                "tokens_per_second": tokens_per_second,
                "scenario": scenario["name"]
            }
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "scenario": scenario["name"]
            }

    def analyze_response_quality(self, model_key: str, scenario: Dict, result: Dict) -> Dict:
        """Analisa qualidade da resposta"""
        if not result["success"]:
            return {"score": 0, "analysis": "Failed to generate response"}
        
        response = result["response"].lower()
        scenario_name = scenario["name"]
        
        score = 0
        analysis_points = []
        
        # Basic response quality checks
        if len(response.strip()) > 10:
            score += 1
            analysis_points.append("Generated substantial response")
        
        if not any(error_word in response for error_word in ["error", "sorry", "cannot", "unable"]):
            score += 1
            analysis_points.append("No obvious error indicators")
        
        # Scenario-specific analysis
        if "function calling" in scenario_name.lower():
            function_indicators = ["get_room_availability", "building", "room", "201", "engineering"]
            found_indicators = [ind for ind in function_indicators if ind in response]
            if found_indicators:
                score += 2
                analysis_points.append(f"Function calling awareness: {found_indicators}")
            
        elif "chain-of-thought" in scenario_name.lower():
            reasoning_indicators = ["first", "then", "therefore", "because", "calculate", "1 pm", "6 pm", "hours"]
            found_reasoning = [ind for ind in reasoning_indicators if ind in response]
            if found_reasoning:
                score += 2
                analysis_points.append(f"Reasoning indicators: {found_reasoning}")
            
            # Check for Qwen3 thinking mode
            if model_key == "qwen3" and "<think>" in result["response"]:
                score += 2
                analysis_points.append("Uses thinking mode (Qwen3 feature)")
        
        elif "json" in scenario_name.lower():
            if "{" in response and "}" in response:
                score += 2
                analysis_points.append("Contains JSON structure")
            try:
                # Try to find and parse JSON in response
                import re
                json_match = re.search(r'\{.*\}', result["response"], re.DOTALL)
                if json_match:
                    json.loads(json_match.group())
                    score += 1
                    analysis_points.append("Valid JSON found")
            except:
                pass
        
        elif "academic" in scenario_name.lower():
            academic_indicators = ["hours", "building", "administration", "contact", "check"]
            found_academic = [ind for ind in academic_indicators if ind in response]
            if found_academic:
                score += 1
                analysis_points.append(f"Academic context awareness: {found_academic}")
        
        return {
            "score": min(score, 5),  # Cap at 5
            "analysis": " | ".join(analysis_points) if analysis_points else "Basic response generated"
        }

    def compare_models(self) -> Dict:
        """Executa comparação completa entre os modelos"""
        print("🔬 QWEN2.5 vs QWEN3 COMPREHENSIVE COMPARISON")
        print("=" * 60)
        
        if not self.check_system_resources():
            return {"error": "Insufficient system resources"}
        
        comparison_results = {}
        
        for model_key in self.models.keys():
            print(f"\n{'='*20} TESTING {self.models[model_key]['display_name']} {'='*20}")
            
            # Load model
            model_config = self.load_model(model_key)
            if not model_config:
                comparison_results[model_key] = {"error": "Failed to load model"}
                continue
            
            model_results = {
                "load_time": model_config["load_time"],
                "memory_used": model_config["memory_used"],
                "model_info": model_config["model_info"],
                "scenarios": {}
            }
            
            total_generation_time = 0
            total_tokens = 0
            scenario_scores = []
            
            # Test all scenarios
            for scenario in self.test_scenarios:
                result = self.run_inference_test(model_config, scenario)
                
                if result["success"]:
                    total_generation_time += result["generation_time"]
                    total_tokens += result["output_tokens"]
                    
                    # Analyze response quality
                    quality_analysis = self.analyze_response_quality(model_key, scenario, result)
                    result["quality_score"] = quality_analysis["score"]
                    result["quality_analysis"] = quality_analysis["analysis"]
                    scenario_scores.append(quality_analysis["score"])
                    
                    print(f"    📊 Quality Score: {quality_analysis['score']}/5")
                    print(f"    📝 Analysis: {quality_analysis['analysis']}")
                else:
                    scenario_scores.append(0)
                
                model_results["scenarios"][scenario["name"]] = result
            
            # Calculate overall metrics
            model_results["avg_tokens_per_second"] = total_tokens / total_generation_time if total_generation_time > 0 else 0
            model_results["avg_quality_score"] = sum(scenario_scores) / len(scenario_scores) if scenario_scores else 0
            model_results["success_rate"] = len([s for s in scenario_scores if s > 0]) / len(scenario_scores)
            
            print(f"\n📊 OVERALL METRICS for {self.models[model_key]['display_name']}:")
            print(f"    Average Speed: {model_results['avg_tokens_per_second']:.1f} tokens/sec")
            print(f"    Average Quality: {model_results['avg_quality_score']:.1f}/5")
            print(f"    Success Rate: {model_results['success_rate']*100:.1f}%")
            
            comparison_results[model_key] = model_results
            
            # Cleanup
            del model_config["model"]
            del model_config["tokenizer"]
            torch.cuda.empty_cache()
            gc.collect()
            
            print(f"\n✅ {self.models[model_key]['display_name']} testing completed\n")
        
        return comparison_results

    def generate_recommendation(self, results: Dict) -> Dict:
        """Gera recomendação baseada nos resultados"""
        if "error" in results:
            return {"recommendation": "Error in comparison", "reason": results["error"]}
        
        models = list(results.keys())
        if len(models) != 2:
            return {"recommendation": "Incomplete comparison", "reason": "Not all models tested"}
        
        qwen25_results = results.get("qwen2.5", {})
        qwen3_results = results.get("qwen3", {})
        
        # Comparison metrics
        comparison = {
            "memory_efficiency": {},
            "performance": {},
            "quality": {},
            "stability": {}
        }
        
        # Memory efficiency
        if "memory_used" in qwen25_results and "memory_used" in qwen3_results:
            qwen25_memory = qwen25_results["memory_used"]
            qwen3_memory = qwen3_results["memory_used"]
            
            comparison["memory_efficiency"] = {
                "qwen2.5": qwen25_memory,
                "qwen3": qwen3_memory,
                "winner": "qwen2.5" if qwen25_memory < qwen3_memory else "qwen3",
                "difference": abs(qwen25_memory - qwen3_memory)
            }
        
        # Performance (speed)
        if "avg_tokens_per_second" in qwen25_results and "avg_tokens_per_second" in qwen3_results:
            qwen25_speed = qwen25_results["avg_tokens_per_second"]
            qwen3_speed = qwen3_results["avg_tokens_per_second"]
            
            comparison["performance"] = {
                "qwen2.5": qwen25_speed,
                "qwen3": qwen3_speed,
                "winner": "qwen2.5" if qwen25_speed > qwen3_speed else "qwen3",
                "difference": abs(qwen25_speed - qwen3_speed)
            }
        
        # Quality
        if "avg_quality_score" in qwen25_results and "avg_quality_score" in qwen3_results:
            qwen25_quality = qwen25_results["avg_quality_score"]
            qwen3_quality = qwen3_results["avg_quality_score"]
            
            comparison["quality"] = {
                "qwen2.5": qwen25_quality,
                "qwen3": qwen3_quality,
                "winner": "qwen2.5" if qwen25_quality > qwen3_quality else "qwen3",
                "difference": abs(qwen25_quality - qwen3_quality)
            }
        
        # Stability (success rate)
        if "success_rate" in qwen25_results and "success_rate" in qwen3_results:
            qwen25_stability = qwen25_results["success_rate"]
            qwen3_stability = qwen3_results["success_rate"]
            
            comparison["stability"] = {
                "qwen2.5": qwen25_stability,
                "qwen3": qwen3_stability,
                "winner": "qwen2.5" if qwen25_stability > qwen3_stability else "qwen3",
                "difference": abs(qwen25_stability - qwen3_stability)
            }
        
        # Calculate overall score
        weights = {
            "memory_efficiency": 0.2,  # Lower memory usage is better
            "performance": 0.25,       # Higher speed is better
            "quality": 0.35,          # Higher quality is better (most important)
            "stability": 0.2          # Higher success rate is better
        }
        
        scores = {"qwen2.5": 0, "qwen3": 0}
        
        for metric, weight in weights.items():
            if metric in comparison and "winner" in comparison[metric]:
                winner = comparison[metric]["winner"]
                scores[winner] += weight
        
        # Determine recommendation
        if scores["qwen3"] > scores["qwen2.5"]:
            recommended_model = "qwen3"
            alternative_model = "qwen2.5"
        else:
            recommended_model = "qwen2.5"
            alternative_model = "qwen3"
        
        score_diff = abs(scores["qwen3"] - scores["qwen2.5"])
        confidence = "High" if score_diff > 0.3 else "Medium" if score_diff > 0.15 else "Low"
        
        return {
            "recommendation": recommended_model,
            "alternative": alternative_model,
            "confidence": confidence,
            "scores": scores,
            "comparison": comparison,
            "reasoning": self._generate_reasoning(comparison, recommended_model)
        }

    def _generate_reasoning(self, comparison: Dict, recommended_model: str) -> List[str]:
        """Gera reasoning para a recomendação"""
        reasoning = []
        
        model_display = "Qwen3-14B" if recommended_model == "qwen3" else "Qwen2.5-14B-Instruct"
        
        for metric, data in comparison.items():
            if "winner" in data and data["winner"] == recommended_model:
                if metric == "memory_efficiency":
                    reasoning.append(f"Better memory efficiency ({data[recommended_model]:.1f}GB vs {data['qwen2.5' if recommended_model == 'qwen3' else 'qwen3']:.1f}GB)")
                elif metric == "performance":
                    reasoning.append(f"Superior speed performance ({data[recommended_model]:.1f} vs {data['qwen2.5' if recommended_model == 'qwen3' else 'qwen3']:.1f} tokens/sec)")
                elif metric == "quality":
                    reasoning.append(f"Higher response quality ({data[recommended_model]:.1f}/5 vs {data['qwen2.5' if recommended_model == 'qwen3' else 'qwen3']:.1f}/5)")
                elif metric == "stability":
                    reasoning.append(f"Better stability ({data[recommended_model]*100:.1f}% vs {data['qwen2.5' if recommended_model == 'qwen3' else 'qwen3']*100:.1f}% success rate)")
        
        # Add specific advantages
        if recommended_model == "qwen3":
            reasoning.append("Native thinking mode for chain-of-thought reasoning")
            reasoning.append("Latest architecture with advanced capabilities (April 2025)")
        else:
            reasoning.append("More mature and stable (September 2024)")
            reasoning.append("Extensive community support and documentation")
        
        return reasoning

    def print_final_report(self, results: Dict, recommendation: Dict):
        """Imprime relatório final"""
        print("\n" + "=" * 80)
        print("🎯 FINAL COMPARISON REPORT")
        print("=" * 80)
        
        # Model specifications
        print("\n📋 MODEL SPECIFICATIONS:")
        for model_key, model_results in results.items():
            if "error" not in model_results:
                info = model_results["model_info"]
                print(f"  {info['display_name']}:")
                print(f"    Release: {info['release_date']}")
                print(f"    Load Time: {model_results['load_time']:.1f}s")
                print(f"    VRAM Usage: {model_results['memory_used']:.1f}GB")
                print(f"    Avg Speed: {model_results['avg_tokens_per_second']:.1f} tokens/sec")
                print(f"    Avg Quality: {model_results['avg_quality_score']:.1f}/5")
                print(f"    Success Rate: {model_results['success_rate']*100:.1f}%")
        
        # Recommendation
        if "error" not in recommendation:
            print(f"\n🏆 RECOMMENDATION: {self.models[recommendation['recommendation']]['display_name']}")
            print(f"📊 Confidence Level: {recommendation['confidence']}")
            print(f"📈 Overall Score: {recommendation['scores'][recommendation['recommendation']]:.2f}")
            
            print(f"\n✅ KEY ADVANTAGES:")
            for reason in recommendation['reasoning']:
                print(f"  • {reason}")
            
            alt_model = self.models[recommendation['alternative']]['display_name']
            print(f"\n🔄 ALTERNATIVE: {alt_model}")
            print(f"📈 Alternative Score: {recommendation['scores'][recommendation['alternative']]:.2f}")
            
            print(f"\n💡 RECOMMENDATION FOR TCC:")
            if recommendation['recommendation'] == 'qwen3':
                print(f"  • Use Qwen3-14B as primary model")
                print(f"  • Leverage native thinking mode for chain-of-thought")
                print(f"  • Implement with latest Qwen-Agent framework")
                print(f"  • Keep Qwen2.5-14B as backup if needed")
            else:
                print(f"  • Use Qwen2.5-14B-Instruct as primary model")
                print(f"  • Benefit from mature ecosystem and documentation")
                print(f"  • Implement with stable Qwen-Agent framework")
                print(f"  • Consider Qwen3-14B for future upgrades")
        
        print("\n" + "=" * 80)

def main():
    """Função principal"""
    comparator = ModelComparator()
    
    print("Starting comprehensive model comparison...")
    results = comparator.compare_models()
    
    if "error" not in results:
        recommendation = comparator.generate_recommendation(results)
        comparator.print_final_report(results, recommendation)
    else:
        print(f"❌ Comparison failed: {results['error']}")

if __name__ == "__main__":
    main()