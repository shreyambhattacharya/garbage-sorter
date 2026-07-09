/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
#include "sorter_hardware.h"
#include "sorter_protocol.h"
#include "sorter_state.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define UART_COMMAND_BUFFER_LENGTH 128
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
TIM_HandleTypeDef htim3;

UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_TIM3_Init(void);
/* USER CODE BEGIN PFP */
static void UART_SendLine(const char *line);
static void UART_SendProtocolResponse(const SorterProtocolResult *result);
static void UART_ProcessCommandLine(const char *command_line);
static void UART_HandleProtocolAction(const SorterProtocolResult *result);
static void UART_HandleSortCommand(const SorterProtocolResult *result);
static void UART_HandleTestCommand(SorterProtocolAction action);
static void UART_SendHardwareResult(const char *test_name, SorterHardwareStatus status);
static void UART_SendUltrasonicReading(const UltrasonicReading *reading);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static void UART_SendLine(const char *line)
{
  HAL_UART_Transmit(&huart2, (uint8_t*)line, strlen(line), HAL_MAX_DELAY);
  HAL_UART_Transmit(&huart2, (uint8_t*)"\r\n", 2, HAL_MAX_DELAY);
}

static void UART_SendProtocolResponse(const SorterProtocolResult *result)
{
  for (uint8_t i = 0; i < result->line_count; i++)
  {
    UART_SendLine(result->lines[i]);
  }
}

static void UART_ProcessCommandLine(const char *command_line)
{
  SorterProtocolResult result;
  SorterProtocol_HandleLine(command_line, &result);
  UART_SendProtocolResponse(&result);
  UART_HandleProtocolAction(&result);
}

static void UART_HandleProtocolAction(const SorterProtocolResult *result)
{
  switch (result->action)
  {
    case SORTER_PROTOCOL_ACTION_SORT:
      UART_HandleSortCommand(result);
      break;
    case SORTER_PROTOCOL_ACTION_TEST_DIVERTERS:
    case SORTER_PROTOCOL_ACTION_TEST_TRAPDOOR:
    case SORTER_PROTOCOL_ACTION_TEST_ULTRASONIC:
    case SORTER_PROTOCOL_ACTION_TEST_DISPLAY:
      UART_HandleTestCommand(result->action);
      break;
    case SORTER_PROTOCOL_ACTION_RESPOND_ONLY:
    default:
      break;
  }
}

static void UART_HandleSortCommand(const SorterProtocolResult *result)
{
  char response_line[UART_COMMAND_BUFFER_LENGTH];
  SorterHardwareStatus hardware_status;

  SorterState_Set(SORTER_STATE_COMMAND_RECEIVED);
  snprintf(response_line, sizeof(response_line), "ACK id=%d", result->command_id);
  UART_SendLine(response_line);
  HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);

  SorterState_Set(SORTER_STATE_SORTING);
  hardware_status = SorterHardware_ExecuteSort(result->class_name);

  if (hardware_status == SORTER_HW_STATUS_OK)
  {
    SorterState_Set(SORTER_STATE_IDLE);
    snprintf(response_line, sizeof(response_line), "DONE id=%d", result->command_id);
    UART_SendLine(response_line);
  }
  else
  {
    SorterState_Set(SORTER_STATE_ERROR);
    snprintf(
        response_line,
        sizeof(response_line),
        "ERROR id=%d message=%s",
        result->command_id,
        SorterHardwareStatus_ToMessage(hardware_status));
    UART_SendLine(response_line);
  }
}

static void UART_HandleTestCommand(SorterProtocolAction action)
{
  SorterHardwareStatus status;
  SorterBinReadings readings;

  switch (action)
  {
    case SORTER_PROTOCOL_ACTION_TEST_DIVERTERS:
      UART_SendLine("STATUS test=TEST_DIVERTERS result=START");
      status = SorterHardware_TestDiverters();
      UART_SendHardwareResult("TEST_DIVERTERS", status);
      break;
    case SORTER_PROTOCOL_ACTION_TEST_TRAPDOOR:
      UART_SendLine("STATUS test=TEST_TRAPDOOR result=START");
      status = SorterHardware_TestTrapdoor();
      UART_SendHardwareResult("TEST_TRAPDOOR", status);
      break;
    case SORTER_PROTOCOL_ACTION_TEST_ULTRASONIC:
      UART_SendLine("STATUS test=TEST_ULTRASONIC result=START");
      status = SorterHardware_TestUltrasonic(&readings);
      if (status != SORTER_HW_STATUS_NOT_CONFIGURED)
      {
        UART_SendUltrasonicReading(&readings.landfill);
        UART_SendUltrasonicReading(&readings.compost);
        UART_SendUltrasonicReading(&readings.recycling);
      }
      UART_SendHardwareResult("TEST_ULTRASONIC", status);
      break;
    case SORTER_PROTOCOL_ACTION_TEST_DISPLAY:
      UART_SendLine("STATUS test=TEST_DISPLAY result=START");
      status = SorterHardware_TestDisplay();
      UART_SendHardwareResult("TEST_DISPLAY", status);
      break;
    default:
      UART_SendLine("ERROR id=0 message=unknown_test");
      break;
  }
}

static void UART_SendHardwareResult(const char *test_name, SorterHardwareStatus status)
{
  char response_line[UART_COMMAND_BUFFER_LENGTH];

  if (status == SORTER_HW_STATUS_OK)
  {
    snprintf(response_line, sizeof(response_line), "DONE test=%s", test_name);
  }
  else
  {
    snprintf(
        response_line,
        sizeof(response_line),
        "ERROR id=0 message=%s",
        SorterHardwareStatus_ToMessage(status));
  }

  UART_SendLine(response_line);
}

static void UART_SendUltrasonicReading(const UltrasonicReading *reading)
{
  char response_line[UART_COMMAND_BUFFER_LENGTH];
  int distance_cm_x100 = (int)((reading->distance_cm * 100.0f) + 0.5f);

  snprintf(
      response_line,
      sizeof(response_line),
      "DISTANCE class=%s valid=%u cm_x100=%d",
      SorterClass_ToString(reading->bin_class),
      reading->valid,
      distance_cm_x100);
  UART_SendLine(response_line);
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  MX_TIM3_Init();
  /* USER CODE BEGIN 2 */
  char rx_buffer[UART_COMMAND_BUFFER_LENGTH];
  uint16_t rx_index = 0;
  uint8_t rx_byte;
  uint8_t discarding_long_command = 0;

  SorterProtocol_Init();
  (void)SorterHardware_Init();
  UART_SendLine("STM32 sorter firmware ready");
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    HAL_UART_Receive(&huart2, &rx_byte, 1, HAL_MAX_DELAY);

    if (rx_byte == '\r' || rx_byte == '\n')
    {
      if (discarding_long_command)
      {
        discarding_long_command = 0;
        rx_index = 0;
      }
      else if (rx_index > 0)
      {
        rx_buffer[rx_index] = '\0';
        UART_ProcessCommandLine(rx_buffer);
        rx_index = 0;
      }
    }
    else if (!discarding_long_command)
    {
      if (rx_index < sizeof(rx_buffer) - 1)
      {
        rx_buffer[rx_index++] = (char)rx_byte;
      }
      else
      {
        rx_index = 0;
        discarding_long_command = 1;
        UART_SendLine("ERROR id=0 message=command_too_long");
      }
    }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE3);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = 16;
  RCC_OscInitStruct.PLL.PLLN = 336;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV4;
  RCC_OscInitStruct.PLL.PLLQ = 2;
  RCC_OscInitStruct.PLL.PLLR = 2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief TIM3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM3_Init(void)
{

  /* USER CODE BEGIN TIM3_Init 0 */

  /* USER CODE END TIM3_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM3_Init 1 */

  /* USER CODE END TIM3_Init 1 */
  htim3.Instance = TIM3;
  htim3.Init.Prescaler = 83;
  htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim3.Init.Period = 19999;
  htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim3) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim3, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim3) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim3, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 1500;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_PWM_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_3) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.Pulse = 0;
  if (HAL_TIM_PWM_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_4) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM3_Init 2 */

  /* USER CODE END TIM3_Init 2 */
  HAL_TIM_MspPostInit(&htim3);

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin : B1_Pin */
  GPIO_InitStruct.Pin = B1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(B1_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : LD2_Pin */
  GPIO_InitStruct.Pin = LD2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LD2_GPIO_Port, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
