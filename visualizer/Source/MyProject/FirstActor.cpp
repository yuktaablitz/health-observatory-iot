// Fill out your copyright notice in the Description page of Project Settings.


#include "FirstActor.h"

#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "PatientStatus.h"


// Sets default values
AFirstActor::AFirstActor()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	RootComponent = Body;

}

// Called when the game starts or when spawned
void AFirstActor::BeginPlay()
{
	Super::BeginPlay();
	
}

// Called every frame
void AFirstActor::Tick(float DeltaTime)
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


