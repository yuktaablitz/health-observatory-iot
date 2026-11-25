// Keeps one WebSocket open to the cloud and remembers the latest risk level per patient.

#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "IWebSocket.h"
#include "WebSocketTestGameInstance.generated.h"

UCLASS(Config = Game)
class MYPROJECT_API UWebSocketTestGameInstance : public UGameInstance
{
	GENERATED_BODY()

public:
	virtual void Init() override;
	virtual void Shutdown() override;

	// Set in Config/DefaultGame.ini so the endpoint is not hard-coded.
	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Health Observatory")
	FString ServerUrl;

	// Latest level for a patient: 0 normal, 1 elevated, 2 high, -1 if nothing received yet.
	UFUNCTION(BlueprintCallable, Category = "Health Observatory")
	int32 GetPatientLevel(const FString& PatientId) const;

	UFUNCTION(BlueprintCallable, Category = "Health Observatory")
	bool IsConnected() const;

	TSharedPtr<IWebSocket> WebSocket;

	// Kept for older Blueprints: last legacy code (3/4/5) and the patient it came from.
	int32 temp = 0;
	FString id;

private:
	void Connect();
	void HandleMessage(const FString& Message);
	void ScheduleReconnect();

	TMap<FString, int32> PatientLevels;
	FTimerHandle ReconnectTimer;
	float ReconnectDelaySeconds = 1.0f;
	bool bShuttingDown = false;
};
