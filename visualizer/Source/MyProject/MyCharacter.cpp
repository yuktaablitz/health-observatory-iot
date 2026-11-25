// Fill out your copyright notice in the Description page of Project Settings.


#include "MyCharacter.h"
#include "Kismet/GameplayStatics.h"
#include "PatientStatus.h"

// Sets default values
AMyCharacter::AMyCharacter()
{
 	// Set this character to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

// Called when the game starts or when spawned
void AMyCharacter::BeginPlay()
{
	Super::BeginPlay();
	
}

// Called every frame
void AMyCharacter::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// Read the latest level for this patient from the game instance and recolour.
	// Fixes: a null WebSocket crashed here before the first connection, and every
	// model showed the last message received instead of its own patient's level.
	UWebSocketTestGameInstance* GameInstance = Cast<UWebSocketTestGameInstance>(UGameplayStatics::GetGameInstance(GetWorld()));
	if (!GameInstance)
	{
		return;
	}
	const int32 NewLevel = GameInstance->GetPatientLevel(PatientId);
	if (NewLevel == PatientStatus::Unknown || NewLevel == Level)
	{
		return;
	}
	Level = NewLevel;
	e = PatientStatus::ToLegacyCode(Level);
	PatientStatus::ToRGB(Level, ValueOne, ValueTwo, ValueThree);
	PatientStatus::ApplyColor(this, ColorParameter, ValueOne, ValueTwo, ValueThree);
}

// Called to bind functionality to input
void AMyCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

}

