// Keeps one WebSocket open to the cloud and remembers the latest risk level per patient.

#include "WebSocketTestGameInstance.h"
#include "WebSocketsModule.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "TimerManager.h"
#include "PatientStatus.h"

void UWebSocketTestGameInstance::Init()
{
	Super::Init();
	bShuttingDown = false;
	if (!FModuleManager::Get().IsModuleLoaded("WebSockets"))
	{
		FModuleManager::Get().LoadModule("WebSockets");
	}
	Connect();
}

void UWebSocketTestGameInstance::Connect()
{
	if (ServerUrl.IsEmpty())
	{
		UE_LOG(LogTemp, Error, TEXT("Health Observatory: set ServerUrl in Config/DefaultGame.ini"));
		return;
	}

	WebSocket = FWebSocketsModule::Get().CreateWebSocket(ServerUrl);
	TWeakObjectPtr<UWebSocketTestGameInstance> WeakThis(this);

	WebSocket->OnConnected().AddLambda([WeakThis]()
	{
		if (!WeakThis.IsValid()) return;
		WeakThis->ReconnectDelaySeconds = 1.0f;
		UE_LOG(LogTemp, Log, TEXT("Health Observatory: connected"));
	});
	WebSocket->OnConnectionError().AddLambda([WeakThis](const FString& Error)
	{
		if (!WeakThis.IsValid()) return;
		UE_LOG(LogTemp, Warning, TEXT("Health Observatory: connection error: %s"), *Error);
		WeakThis->ScheduleReconnect();
	});
	WebSocket->OnClosed().AddLambda([WeakThis](int32 StatusCode, const FString& Reason, bool bWasClean)
	{
		if (!WeakThis.IsValid()) return;
		UE_LOG(LogTemp, Warning, TEXT("Health Observatory: closed (%d) %s"), StatusCode, *Reason);
		WeakThis->ScheduleReconnect();
	});
	WebSocket->OnMessage().AddLambda([WeakThis](const FString& Message)
	{
		if (WeakThis.IsValid()) WeakThis->HandleMessage(Message);
	});

	WebSocket->Connect();
}

void UWebSocketTestGameInstance::HandleMessage(const FString& Message)
{
	// Expected: {"patient_id":"bed-01","level":2,"status":"high - check-up needed","temperature_c":31.6,"ts":...}
	TSharedPtr<FJsonObject> Json;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Message);
	if (!FJsonSerializer::Deserialize(Reader, Json) || !Json.IsValid())
	{
		UE_LOG(LogTemp, Warning, TEXT("Health Observatory: ignored non-JSON message"));
		return;
	}

	FString PatientId;
	double Level = 0.0;
	if (!Json->TryGetStringField(TEXT("patient_id"), PatientId) ||
		!Json->TryGetNumberField(TEXT("level"), Level))
	{
		UE_LOG(LogTemp, Warning, TEXT("Health Observatory: message missing patient_id or level"));
		return;
	}

	const int32 LevelInt = FMath::Clamp(FMath::RoundToInt(Level), (int32)PatientStatus::Normal, (int32)PatientStatus::High);
	PatientLevels.Add(PatientId, LevelInt);
	temp = PatientStatus::ToLegacyCode(LevelInt);
	id = PatientId;
}

int32 UWebSocketTestGameInstance::GetPatientLevel(const FString& PatientId) const
{
	const int32* Found = PatientLevels.Find(PatientId);
	return Found ? *Found : PatientStatus::Unknown;
}

bool UWebSocketTestGameInstance::IsConnected() const
{
	return WebSocket.IsValid() && WebSocket->IsConnected();
}

void UWebSocketTestGameInstance::ScheduleReconnect()
{
	if (bShuttingDown || GetTimerManager().IsTimerActive(ReconnectTimer))
	{
		return;
	}
	const float Delay = ReconnectDelaySeconds;
	ReconnectDelaySeconds = FMath::Min(ReconnectDelaySeconds * 2.0f, 30.0f);
	UE_LOG(LogTemp, Log, TEXT("Health Observatory: reconnecting in %.0f s"), Delay);
	GetTimerManager().SetTimer(ReconnectTimer, FTimerDelegate::CreateUObject(this, &UWebSocketTestGameInstance::Connect), Delay, false);
}

void UWebSocketTestGameInstance::Shutdown()
{
	bShuttingDown = true;
	if (WebSocket.IsValid())
	{
		WebSocket->OnClosed().Clear();
		WebSocket->OnConnectionError().Clear();
		if (WebSocket->IsConnected())
		{
			WebSocket->Close();
		}
	}
	Super::Shutdown();
}
