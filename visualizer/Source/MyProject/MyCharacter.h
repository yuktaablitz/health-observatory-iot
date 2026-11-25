// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "WebSocketTestGameInstance.h"
#include "MyCharacter.generated.h"

UCLASS()
class MYPROJECT_API AMyCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	// Sets default values for this character's properties
	AMyCharacter();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WebSocket variables")
		float ValueOne;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WebSocket variables")
		float ValueTwo;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WebSocket variables")
		float ValueThree;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WebSocket variables")
		int32 e;

	// Which patient this model shows; must match PATIENT_ID in the ESP32 config.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Health Observatory")
		FString PatientId = TEXT("bed-01");

	// Latest level for PatientId: 0 normal, 1 elevated, 2 high, -1 unknown.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health Observatory")
		int32 Level = -1;

	// Vector parameter on the model's material that receives the colour; set to None
	// if a Blueprint applies ValueOne/ValueTwo/ValueThree itself.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Health Observatory")
		FName ColorParameter = TEXT("Color");

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

	// Called to bind functionality to input
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

};
