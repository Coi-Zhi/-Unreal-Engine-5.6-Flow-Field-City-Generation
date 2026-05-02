// Copyright Epic Games, Inc. All Rights Reserved.

#include "City_Generation_Tool_Bar.h"
#include "City_Generation_Tool_BarStyle.h"
#include "City_Generation_Tool_BarCommands.h"
#include "Misc/MessageDialog.h"
#include "ToolMenus.h"

#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"

static const FName City_Generation_Tool_BarTabName("City_Generation_Tool_Bar");

#define LOCTEXT_NAMESPACE "FCity_Generation_Tool_BarModule"

void FCity_Generation_Tool_BarModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	
	FCity_Generation_Tool_BarStyle::Initialize();
	FCity_Generation_Tool_BarStyle::ReloadTextures();

	FCity_Generation_Tool_BarCommands::Register();
	
	PluginCommands = MakeShareable(new FUICommandList);

	PluginCommands->MapAction(
		FCity_Generation_Tool_BarCommands::Get().PluginAction,
		FExecuteAction::CreateRaw(this, &FCity_Generation_Tool_BarModule::PluginButtonClicked),
		FCanExecuteAction());

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FCity_Generation_Tool_BarModule::RegisterMenus));
}

void FCity_Generation_Tool_BarModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	UToolMenus::UnRegisterStartupCallback(this);

	UToolMenus::UnregisterOwner(this);

	FCity_Generation_Tool_BarStyle::Shutdown();

	FCity_Generation_Tool_BarCommands::Unregister();
}

void FCity_Generation_Tool_BarModule::PluginButtonClicked()
{
	// 1. 獲取 UE 的 Editor Utility Subsystem
	UEditorUtilitySubsystem* EditorUtilitySubsystem = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();

	// 2. 設定你個 EUW 嘅真實路徑 
	// ⚠️ 獲取方法：喺 UE 內容瀏覽器 Right-Click 你個 EUW -> 選擇 "Copy Reference"
	// 貼上嚟之後，刪除前面嘅 "EditorUtilityWidgetBlueprint'" 同後面嘅單引號 "'"
	// 正確格式應該類似："/City_Generate/EUW_Generation.EUW_Generation"

	FString WidgetPath = TEXT("/City_Generation_Tool_Bar/Generation.Generation");
	
	UObject* BlueprintObj = StaticLoadObject(UObject::StaticClass(), nullptr, *WidgetPath);

	// 3. 轉換型別並打開它
	if (UEditorUtilityWidgetBlueprint* EditorWidget = Cast<UEditorUtilityWidgetBlueprint>(BlueprintObj))
	{
		EditorUtilitySubsystem->SpawnAndRegisterTab(EditorWidget);
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("載入 EUW 失敗！請檢查路徑：%s"), *WidgetPath);
	}
}

void FCity_Generation_Tool_BarModule::RegisterMenus()
{
    // Owner 會喺清理時用到
    FToolMenuOwnerScoped OwnerScoped(this);

    // --- 修改 1: Window 菜單 (增加橫線同分組標題) ---
    {
        UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
        if (Menu)
        {
            // 呢度用 AddSection 嚟開一個新分組
            // "CityGeneration" 是 ID
            // FText::FromString("City Generation") 呢個字就會好似 "LOG" 咁樣顯示出嚟
            FToolMenuSection& Section = Menu->AddSection(
                "CityGenerationSection",
                FText::FromString("City Generation"), // 呢個就係你想要嘅標題
                FToolMenuInsert("WindowLayout", EToolMenuInsertType::After)
            );

            Section.AddMenuEntryWithCommandList(FCity_Generation_Tool_BarCommands::Get().PluginAction, PluginCommands);
        }
    }

    // --- 修改 2: Toolbar 工具欄 (修正編譯錯誤) ---
    {
        UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.PlayToolBar");
        if (ToolbarMenu)
        {
            FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("PluginTools");
            
            // 註冊掣
            FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(FCity_Generation_Tool_BarCommands::Get().PluginAction));
            Entry.SetCommandList(PluginCommands);
            
            // 【核心修正】：UE 5.x 入面，無論係 Menu 定 Toolbar，屬性名都係 Label
            Entry.Label = FText::FromString("City Gen"); 
            
            // 如果你想增加識別度，可以加埋 ToolTip（滑鼠指住時顯示嘅文字）
            Entry.ToolTip = FText::FromString("Open the City Generation Tool Window");
        }
    }
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FCity_Generation_Tool_BarModule, City_Generation_Tool_Bar)