// Risk levels sent by the cloud and the colours each patient model shows.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/MeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace PatientStatus
{
	// Levels from cloud/functions/vitals.py: 0 normal, 1 elevated, 2 high.
	constexpr int32 Unknown = -1;
	constexpr int32 Normal = 0;
	constexpr int32 Elevated = 1;
	constexpr int32 High = 2;

	// The original Blueprints read the legacy codes 3/4/5 from `e`, so keep emitting them.
	inline int32 ToLegacyCode(int32 Level) { return Level + 3; }

	// RGB in 0-255 (the range the existing Blueprints expect in ValueOne/Two/Three).
	inline void ToRGB(int32 Level, float& R, float& G, float& B)
	{
		switch (Level)
		{
		case Normal:   R = 0.0f;   G = 255.0f; B = 0.0f; break; // green
		case Elevated: R = 255.0f; G = 255.0f; B = 0.0f; break; // yellow
		case High:     R = 255.0f; G = 0.0f;   B = 0.0f; break; // red
		default:       break;                                    // unknown: leave colour as is
		}
	}

	// Tints every material slot on the actor's meshes through a vector parameter
	// (default name "Color"), so the model changes colour without needing a Blueprint.
	// The material needs a Vector Parameter with that name wired to Base Color.
	inline void ApplyColor(AActor* Actor, FName ParameterName, float R, float G, float B)
	{
		if (!Actor || ParameterName.IsNone())
		{
			return;
		}
		const FLinearColor Color(R / 255.0f, G / 255.0f, B / 255.0f);
		TArray<UMeshComponent*> Meshes;
		Actor->GetComponents<UMeshComponent>(Meshes);
		for (UMeshComponent* Mesh : Meshes)
		{
			for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
			{
				// Reuses the dynamic instance after the first call instead of creating a new one.
				if (UMaterialInstanceDynamic* Mid = Mesh->CreateDynamicMaterialInstance(Slot))
				{
					Mid->SetVectorParameterValue(ParameterName, Color);
				}
			}
		}
	}
}
